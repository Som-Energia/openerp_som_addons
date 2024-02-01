# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import timedelta, date, datetime
from giscedata_switching.tests.common_tests import TestSwitchingImport
from osv import osv, fields
from som_polissa.exceptions import exceptions
import mock


class TestChangeToPeriodes(TestSwitchingImport):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def open_polissa(self, xml_id, indexed=False):
        polissa_obj = self.pool.get("giscedata.polissa")
        imd_obj = self.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", xml_id
        )[1]

        if indexed:
            polissa_obj.write(
                self.cursor,
                self.uid,
                polissa_id,
                {
                    "mode_facturacio": "index",
                    "mode_facturacio_generacio": "index",
                },
            )

        polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])

        return polissa_id

    def test_change_to_periodes_inactive_polissa(self):
        imd_obj = self.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_o = self.pool.get("wizard.change.to.indexada")

        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)
        with self.assertRaises(exceptions.PolissaNotActive) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(error.exception.to_dict()["error"], u"Pòlissa 0018 not active")

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_change_to_periodes_modcon_pendent_polissa(self, mocked_send_mail):
        wiz_o = self.pool.get("wizard.change.to.indexada")
        polissa_id = self.open_polissa("polissa_tarifa_018", indexed=True)
        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        with self.assertRaises(exceptions.PolissaModconPending) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(
            error.exception.to_dict()["error"], u"Pòlissa 0018 already has a pending modcon"
        )
        IrModel = self.pool.get("ir.model.data")

        template_id = IrModel.get_object_reference(
            self.cursor, self.uid, "som_indexada", "email_canvi_tarifa_a_indexada"
        )[1]
        account_obj = self.pool.get("poweremail.core_accounts")
        email_from = account_obj.search(
            self.cursor, self.uid, [("email_id", "=", "info@somenergia.coop")]
        )[0]
        expected_ctx = {
            "active_ids": [polissa_id],
            "active_id": polissa_id,
            "template_id": template_id,
            "src_model": "giscedata.polissa",
            "src_rec_ids": [polissa_id],
            "from": email_from,
            "state": "single",
            "priority": "0",
        }
        mocked_send_mail.assert_called_with(self.cursor, self.uid, mock.ANY, expected_ctx)

    def test_change_to_periodes_already_period_polissa(self):
        wiz_o = self.pool.get("wizard.change.to.indexada")
        polissa_id = self.open_polissa("polissa_tarifa_018")
        polissa_obj = self.pool.get("giscedata.polissa")

        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)
        with self.assertRaises(exceptions.PolissaAlreadyPeriod) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(error.exception.to_dict()["error"], u"Pòlissa 0018 already period")

    def test_change_to_periodes_tariff_code_not_supported(self):
        wiz_o = self.pool.get("wizard.change.to.indexada")
        polissa_id = self.open_polissa("polissa_0001", indexed=True)
        polissa_obj = self.pool.get("giscedata.polissa")
        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)
        with self.assertRaises(exceptions.TariffCodeNotSupported) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(
            error.exception.to_dict()["error"], u"Change with tariff code 2.0A not supported"
        )

    def test_change_to_periodes_atr_en_curs_polissa(self):
        polissa_obj = self.pool.get("giscedata.polissa")
        wiz_o = self.pool.get("wizard.change.to.indexada")
        polissa_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(self.txn, context=None)
        polissa_obj.write(
            self.cursor,
            self.uid,
            polissa_id,
            {
                "mode_facturacio": "index",
                "mode_facturacio_generacio": "index",
            },
        )
        polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])
        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)
        step_id = self.create_case_and_step(self.cursor, self.uid, polissa_id, "M1", "01")
        with self.assertRaises(exceptions.PolissaSimultaneousATR) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(error.exception.to_dict()["error"], u"Pòlissa 0018 with simultaneous ATR")

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_change_to_periodes_one_polissa(self, mocked_send_mail):
        polissa_obj = self.pool.get("giscedata.polissa")
        modcon_obj = self.pool.get("giscedata.polissa.modcontractual")
        wiz_o = self.pool.get("wizard.change.to.indexada")
        IrModel = self.pool.get("ir.model.data")

        polissa_id = self.open_polissa("polissa_tarifa_018", indexed=True)
        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][0]
        prev_modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][1]

        new_pricelist_id = IrModel._get_obj(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        ).id

        modcon_act = modcon_obj.read(
            self.cursor,
            self.uid,
            modcontactual_id,
            [
                "data_inici",
                "data_final",
                "mode_facturacio",
                "mode_facturacio_generacio",
                "llista_preu",
                "active",
                "state",
                "modcontractual_ant",
            ],
        )
        modcon_act.pop("id")
        modcon_act["llista_preu"] = modcon_act["llista_preu"][0]
        modcon_act["modcontractual_ant"] = modcon_act["modcontractual_ant"][0]

        self.assertEquals(
            modcon_act,
            {
                "data_inici": datetime.strftime(date.today() + timedelta(days=1), "%Y-%m-%d"),
                "data_final": datetime.strftime(date.today() + timedelta(days=365), "%Y-%m-%d"),
                "mode_facturacio": "atr",
                "mode_facturacio_generacio": "atr",
                "llista_preu": new_pricelist_id,
                "active": True,
                "state": "pendent",
                "modcontractual_ant": prev_modcontactual_id,
            },
        )
        IrModel = self.pool.get("ir.model.data")

        template_id = IrModel.get_object_reference(
            self.cursor, self.uid, "som_indexada", "email_canvi_tarifa_a_indexada"
        )[1]
        account_obj = self.pool.get("poweremail.core_accounts")
        email_from = account_obj.search(
            self.cursor, self.uid, [("email_id", "=", "info@somenergia.coop")]
        )[0]
        expected_ctx = {
            "active_ids": [polissa_id],
            "active_id": polissa_id,
            "template_id": template_id,
            "src_model": "giscedata.polissa",
            "src_rec_ids": [polissa_id],
            "from": email_from,
            "state": "single",
            "priority": "0",
        }
        mocked_send_mail.assert_called_with(self.cursor, self.uid, mock.ANY, expected_ctx)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_change_to_periodes_one_30td_polissa(self, mocked_send_mail):
        polissa_obj = self.pool.get("giscedata.polissa")
        modcon_obj = self.pool.get("giscedata.polissa.modcontractual")
        wiz_o = self.pool.get("wizard.change.to.indexada")
        IrModel = self.pool.get("ir.model.data")

        polissa_id = self.open_polissa("polissa_tarifa_019", indexed=True)
        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][0]
        prev_modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][1]

        new_pricelist_id = IrModel._get_obj(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_30td_peninsula"
        ).id

        modcon_act = modcon_obj.read(
            self.cursor,
            self.uid,
            modcontactual_id,
            [
                "data_inici",
                "data_final",
                "mode_facturacio",
                "mode_facturacio_generacio",
                "llista_preu",
                "active",
                "state",
                "modcontractual_ant",
            ],
        )
        modcon_act.pop("id")
        modcon_act["llista_preu"] = modcon_act["llista_preu"][0]
        modcon_act["modcontractual_ant"] = modcon_act["modcontractual_ant"][0]

        self.assertEquals(
            modcon_act,
            {
                "data_inici": datetime.strftime(date.today() + timedelta(days=1), "%Y-%m-%d"),
                "data_final": datetime.strftime(date.today() + timedelta(days=365), "%Y-%m-%d"),
                "mode_facturacio": "atr",
                "mode_facturacio_generacio": "atr",
                "llista_preu": new_pricelist_id,
                "active": True,
                "state": "pendent",
                "modcontractual_ant": prev_modcontactual_id,
            },
        )
        IrModel = self.pool.get("ir.model.data")

        template_id = IrModel.get_object_reference(
            self.cursor, self.uid, "som_indexada", "email_canvi_tarifa_a_indexada"
        )[1]
        account_obj = self.pool.get("poweremail.core_accounts")
        email_from = account_obj.search(
            self.cursor, self.uid, [("email_id", "=", "info@somenergia.coop")]
        )[0]
        expected_ctx = {
            "active_ids": [polissa_id],
            "active_id": polissa_id,
            "template_id": template_id,
            "src_model": "giscedata.polissa",
            "src_rec_ids": [polissa_id],
            "from": email_from,
            "state": "single",
            "priority": "0",
        }
        mocked_send_mail.assert_called_with(self.cursor, self.uid, mock.ANY, expected_ctx)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_change_to_periodes_one_polissa_with_auto(self, mocked_send_mail):
        polissa_obj = self.pool.get("giscedata.polissa")
        modcon_obj = self.pool.get("giscedata.polissa.modcontractual")
        wiz_o = self.pool.get("wizard.change.to.indexada")
        IrModel = self.pool.get("ir.model.data")

        polissa_id = self.open_polissa("polissa_tarifa_018_autoconsum_41", indexed=True)
        context = {"active_id": polissa_id, "change_type": "from_index_to_period"}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][0]
        prev_modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][1]

        new_pricelist_id = IrModel._get_obj(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        ).id

        modcon_act = modcon_obj.read(
            self.cursor,
            self.uid,
            modcontactual_id,
            [
                "data_inici",
                "data_final",
                "mode_facturacio",
                "mode_facturacio_generacio",
                "llista_preu",
                "active",
                "state",
                "modcontractual_ant",
                "autoconsumo",
            ],
        )
        modcon_act.pop("id")
        modcon_act["llista_preu"] = modcon_act["llista_preu"][0]
        modcon_act["modcontractual_ant"] = modcon_act["modcontractual_ant"][0]

        self.assertEquals(
            modcon_act,
            {
                "data_inici": datetime.strftime(date.today() + timedelta(days=1), "%Y-%m-%d"),
                "data_final": datetime.strftime(date.today() + timedelta(days=365), "%Y-%m-%d"),
                "mode_facturacio": "atr",
                "mode_facturacio_generacio": "atr",
                "llista_preu": new_pricelist_id,
                "active": True,
                "state": "pendent",
                "modcontractual_ant": prev_modcontactual_id,
                "autoconsumo": "41",
            },
        )
        IrModel = self.pool.get("ir.model.data")

        template_id = IrModel.get_object_reference(
            self.cursor, self.uid, "som_indexada", "email_canvi_tarifa_a_indexada"
        )[1]
        account_obj = self.pool.get("poweremail.core_accounts")
        email_from = account_obj.search(
            self.cursor, self.uid, [("email_id", "=", "info@somenergia.coop")]
        )[0]
        expected_ctx = {
            "active_ids": [polissa_id],
            "active_id": polissa_id,
            "template_id": template_id,
            "src_model": "giscedata.polissa",
            "src_rec_ids": [polissa_id],
            "from": email_from,
            "state": "single",
            "priority": "0",
        }
        mocked_send_mail.assert_called_with(self.cursor, self.uid, mock.ANY, expected_ctx)
