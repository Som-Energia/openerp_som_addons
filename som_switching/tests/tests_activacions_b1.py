# -*- coding: utf-8 -*-
from destral.transaction import Transaction
import mock
from giscedata_switching.tests.common_tests import TestSwitchingImport
from destral.patch import PatchNewCursors


class TestActivacioB1(TestSwitchingImport):
    def setUp(self):
        self.pool = self.openerp.pool
        self.Polissa = self.pool.get("giscedata.polissa")
        self.Switching = self.pool.get("giscedata.switching")
        self.User = self.pool.get("res.users")
        self.Company = self.pool.get("res.company")
        self.ResPartner = self.pool.get("res.partner")
        self.ResConfig = self.openerp.pool.get("res.config")
        self.ResPartnerAddress = self.pool.get("res.partner.address")
        self.B101 = self.openerp.pool.get("giscedata.switching.b1.01")
        self.ResConfig = self.openerp.pool.get("res.config")
        self.IrModelData = self.openerp.pool.get("ir.model.data")

    def get_b1_01(self, txn, contract_id, context=None):
        if not context:
            context = {}
        uid = txn.user
        cursor = txn.cursor
        self.switch(txn, "comer")
        context["extra_vals"] = {
            "data_alta": "2017-01-31",
            "lot_facturacio": False,
            "data_baixa": False,
        }

        # create step 01
        self.change_polissa_comer(txn)
        self.update_polissa_distri(txn)
        self.activar_polissa_CUPS(txn, context=context)
        step_id = self.create_case_and_step(cursor, uid, contract_id, "B1", "01")

        sw_id = self.B101.read(cursor, uid, step_id, ["sw_id"])["sw_id"][0]
        return self.Switching.browse(cursor, uid, sw_id, {"browse_reference": True})

    def get_b1_02(self, txn, contract_id):
        uid = txn.user
        cursor = txn.cursor
        b1 = self.get_b1_01(txn, contract_id)

        self.create_step(cursor, uid, b1, "B1", "02", {"whereiam": "distri"})
        b1 = self.Switching.browse(cursor, uid, b1.id, {"browse_reference": True})
        b102 = b1.step_ids[-1].pas_id
        b102.write({"data_activacio": "2021-08-01"})

        return b1

    def get_b1_05(self, txn, contract_id, context=None):
        if not context:
            context = {}
        uid = txn.user
        cursor = txn.cursor
        context["extra_vals"] = {
            "data_alta": "2017-01-31",
            "lot_facturacio": False,
            "data_baixa": False,
        }

        b1 = self.get_b1_02(txn, contract_id)
        self.assertEqual(b1.step_id.name, "02")

        self.create_step(cursor, uid, b1, "B1", "05", {"whereiam": "distri"})
        b1 = self.Switching.browse(cursor, uid, b1.id, {"browse_reference": True})
        b105 = b1.step_ids[-1].pas_id
        b105.write({"data_activacio": "2021-08-01"})

        return b1

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_b1_05_baixa_mailchimp_ok(self, mock_unsubscribe):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "1")

            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ["titular"])["titular"][0]
            pol_ids = self.Polissa.search(
                cursor, uid, [("id", "!=", contract_id), ("titular", "=", old_partner_id)]
            )
            self.Polissa.write(cursor, uid, pol_ids, {"titular": False})

            b1 = self.get_b1_05(txn, contract_id)

            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, b1)

            mock_unsubscribe.assert_called_with(mock.ANY, uid, old_partner_id, context=mock.ANY)

            expected_result = (
                u"[Baixa Mailchimp] S'ha iniciat el procés de baixa "
                u"per l'antic titular (ID %d)" % (old_partner_id)
            )
            history_line_desc = [line["description"] for line in b1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_b1_05_baixa_mailchimp_error__more_than_one_contract(self, mock_unsubscribe):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "1")

            contract_id = self.get_contract_id(txn, "polissa_tarifa_018")
            contract_obj_id = self.Polissa.browse(cursor, uid, [contract_id])[0]
            if contract_obj_id.state == "esborrany":
                contract_obj_id.send_signal(["validar", "contracte"])

            b1 = self.get_b1_05(txn, contract_id, {"polissa_xml_id": "polissa_tarifa_018"})
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, b1)

            self.assertTrue(not mock_unsubscribe.called)

            expected_result = (
                u"[Baixa Mailchimp] No s'ha iniciat el procés de baixa "
                u"perque l'antic titular encara té pòlisses associades"
            )
            history_line_desc = [line["description"] for line in b1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_b1_05_baixa_mailchimp_error__active_contract(self, mock_unsubscribe):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "0")
            contract_id = self.get_contract_id(txn)

            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ["titular"])["titular"][0]
            pol_ids = self.Polissa.search(
                cursor, uid, [("id", "!=", contract_id), ("titular", "=", old_partner_id)]
            )
            self.Polissa.write(cursor, uid, pol_ids, {"titular": False})

            b1 = self.get_b1_05(txn, contract_id)

            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, b1)

            self.assertTrue(not mock_unsubscribe.called)

            expected_result = (
                u"[Baixa Mailchimp] No s'ha donat de baixa "
                u"el titular perquè la pòlissa està activa."
            )
            history_line_desc = [line["description"] for line in b1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))
