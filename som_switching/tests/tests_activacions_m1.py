# -*- coding: utf-8 -*-
from destral.transaction import Transaction
import mock
from giscedata_switching.tests.common_tests import TestSwitchingImport
from destral.patch import PatchNewCursors


class TestActivacioM1(TestSwitchingImport):
    def setUp(self):
        self.pool = self.openerp.pool
        self.Polissa = self.pool.get("giscedata.polissa")
        self.Switching = self.pool.get("giscedata.switching")
        self.ResPartner = self.pool.get("res.partner")
        self.ResPartnerAddress = self.pool.get("res.partner.address")
        self.M101 = self.openerp.pool.get("giscedata.switching.m1.01")
        self.ResConfig = self.openerp.pool.get("res.config")
        self.IrModelData = self.openerp.pool.get("ir.model.data")

    def get_m1_01_ct(self, txn, contract_id, tipus, context=None):
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
        self.activar_polissa_CUPS(txn, context)
        step_id = self.create_case_and_step(cursor, uid, contract_id, "M1", "01")

        pt_obj = self.openerp.pool.get("payment.type")
        step = self.M101.browse(cursor, uid, step_id)

        step.sw_id.titular_polissa.id
        new_partner_id = self.IrModelData.get_object_reference(
            cursor, uid, "som_polissa_soci", "res_partner_nosoci2"
        )[1]
        new_partner_vat = self.ResPartner.read(cursor, uid, new_partner_id, ["vat"])["vat"][2:]
        new_partner_address = self.ResPartnerAddress.search(
            cursor, uid, [("partner_id", "=", new_partner_id)]
        )[0]
        m101 = self.M101.browse(cursor, uid, step_id)
        m101.write(
            {
                "sollicitudadm": "S",
                "canvi_titular": tipus,
                "tarifaATR": "003",
                "direccio_pagament": new_partner_address,
                "direccio_notificacio": new_partner_address,
                "codi_document": new_partner_vat,
                "tipo_pago": pt_obj.search(cursor, uid, [], limit=1)[0],
            }
        )
        other_polissa_id = self.Polissa.search(
            cursor, uid, [("id", "!=", contract_id), ("state", "=", "esborrany")], limit=1
        )[-1]
        self.Switching.write(
            cursor, uid, m101.sw_id.id, {"ref": "giscedata.polissa,{}".format(other_polissa_id)}
        )
        return self.Switching.browse(cursor, uid, m101.sw_id.id, {"browse_reference": True})

    def get_m1_02_ct(self, txn, contract_id, tipus, context=None):
        uid = txn.user
        cursor = txn.cursor
        m1 = self.get_m1_01_ct(txn, contract_id, tipus)

        m1.cups_polissa_id

        self.ResConfig.set(cursor, uid, "sw_m1_S_with_service_order", "0")
        self.ResConfig.set(cursor, uid, "sw_m1_owner_change_subrogacio_new_contract", "0")
        self.create_step(cursor, uid, m1, "M1", "02", {"whereiam": "distri"})
        m1 = self.Switching.browse(cursor, uid, m1.id, {"browse_reference": True})
        m102 = m1.step_ids[-1].pas_id
        m102.write({"data_activacio": "2021-08-01"})

        return m1

    def get_m1_05_traspas(self, txn, contract_id, context=None):
        uid = txn.user
        cursor = txn.cursor
        m1 = self.get_m1_02_ct(txn, contract_id, "T")
        self.ResConfig.set(cursor, uid, "sw_m1_owner_change_auto", "1")
        self.create_step(cursor, uid, m1, "M1", "05", context=None)
        m1 = self.Switching.browse(cursor, uid, m1.id, {"browse_reference": True})
        m105 = m1.step_ids[-1].pas_id
        m105.write({"data_activacio": "2021-08-05"})

        return m1

    @mock.patch("som_polissa_soci.res_partner.ResPartner.arxiva_client_mailchimp_async")
    def test_ct_subrogacio_baixa_mailchimp_ok(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ["titular"])["titular"][0]
            pol_ids = self.Polissa.search(
                cursor, uid, [("id", "!=", contract_id), ("titular", "=", old_partner_id)]
            )
            self.Polissa.write(cursor, uid, pol_ids, {"titular": False})

            m1 = self.get_m1_02_ct(txn, contract_id, "S")
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, m1)

            mock_function.assert_called_with(mock.ANY, uid, old_partner_id)

            expected_result = (
                u"[Baixa Mailchimp] S'ha iniciat el procés de baixa "
                u"per l'antic titular (ID %d)" % (old_partner_id)
            )
            history_line_desc = [line["description"] for line in m1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.res_partner.ResPartner.arxiva_client_mailchimp_async")
    def test_ct_subrogacio_baixa_mailchimp_error__more_than_one_contract(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            contract_id = self.get_contract_id(txn, "polissa_tarifa_018")

            m1 = self.get_m1_02_ct(txn, contract_id, "S", {"polissa_xml_id": "polissa_tarifa_018"})
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, m1)

            self.assertTrue(not mock_function.called)

            expected_result = (
                u"[Baixa Mailchimp] No s'ha iniciat el procés de baixa "
                u"perque l'antic titular encara té pòlisses associades"
            )
            history_line_desc = [line["description"] for line in m1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.res_partner.ResPartner.arxiva_client_mailchimp_async")
    @mock.patch(
        "giscedata_lectures_switching.giscedata_lectures.GiscedataLecturesSwitchingHelper.move_meters_of_contract"  # noqa: E501
    )
    def test_ct_traspas_baixa_mailchimp_ok(self, mock_lectures, mock_mailchimp_function):
        with Transaction().start(self.database) as txn:

            cursor = txn.cursor
            uid = txn.user

            mock_lectures.return_value = []
            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ["titular"])["titular"][0]
            pol_ids = self.Polissa.search(
                cursor, uid, [("id", "!=", contract_id), ("titular", "=", old_partner_id)]
            )
            self.Polissa.write(cursor, uid, pol_ids, {"titular": False, "data_baixa": "2099-01-01"})

            m1 = self.get_m1_05_traspas(txn, contract_id)
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, m1)

            mock_mailchimp_function.assert_called_with(mock.ANY, uid, old_partner_id)

            expected_result = (
                u"[Baixa Mailchimp] S'ha iniciat el procés de baixa "
                u"per l'antic titular (ID %d)" % (old_partner_id)
            )
            history_line_desc = [line["description"] for line in m1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.res_partner.ResPartner.arxiva_client_mailchimp_async")
    @mock.patch(
        "giscedata_lectures_switching.giscedata_lectures.GiscedataLecturesSwitchingHelper.move_meters_of_contract"  # noqa: E501
    )
    def test_ct_traspas_baixa_mailchimp_error__more_than_one_contract(
        self, mock_lectures, mock_function
    ):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            mock_lectures.return_value = []
            contract_id = self.get_contract_id(txn, "polissa_tarifa_018")
            # actualitze 'data_baixa' per a que no falle el test per la restricció de dates
            # 'giscedata_polissa_modcontractual_date_coherence'
            contract_002_id = self.get_contract_id(txn, "polissa_0002")
            self.Polissa.write(cursor, uid, [contract_002_id], {"data_baixa": "2099-01-01"})

            m1 = self.get_m1_05_traspas(txn, contract_id, {"polissa_xml_id": "polissa_tarifa_018"})
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, m1)

            self.assertTrue(not mock_function.called)

            expected_result = (
                u"[Baixa Mailchimp] No s'ha iniciat el procés de baixa "
                u"perque l'antic titular encara té pòlisses associades"
            )
            history_line_desc = [line["description"] for line in m1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))
