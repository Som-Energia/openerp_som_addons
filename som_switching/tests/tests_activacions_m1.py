# -*- coding: utf-8 -*-
from destral.transaction import Transaction
import mock
from giscedata_switching.tests.common_tests import TestSwitchingImport
from destral.patch import PatchNewCursors
from addons import get_module_resource


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
        self.activar_polissa_CUPS(txn, context=context)
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
            cursor, uid,
            [
                ("id", "!=", contract_id),
                ("state", "=", "esborrany"),
                ("tarifa_codi", "=", "2.0TD")
            ], limit=1
        )[-1]
        self.Switching.write(
            cursor, uid, m101.sw_id.id, {"ref": "giscedata.polissa,{}".format(other_polissa_id)}
        )
        return self.Switching.browse(cursor, uid, m101.sw_id.id, {"browse_reference": True})

    def get_m1_02_ct(self, txn, contract_id, tipus, context=None):
        if not context:
            context = {}
        uid = txn.user
        cursor = txn.cursor
        m1 = self.get_m1_01_ct(txn, contract_id, tipus)

        m1.cups_polissa_id

        self.ResConfig.set(cursor, uid, "sw_m1_S_with_service_order", "0")
        self.ResConfig.set(cursor, uid, "sw_m1_owner_change_subrogacio_new_contract", "0")
        self.create_step(cursor, uid, m1, "M1", "02", {"whereiam": "distri"})
        m1 = self.Switching.browse(cursor, uid, m1.id, {"browse_reference": True})
        m102 = m1.step_ids[-1].pas_id
        m102.write({"data_activacio": context.get("data_activacio", "2021-08-01")})

        return m1

    def get_m1_05_traspas(self, txn, contract_id, context=None):
        if not context:
            context = {}
        uid = txn.user
        cursor = txn.cursor
        m1 = self.get_m1_02_ct(txn, contract_id, "T")
        self.ResConfig.set(cursor, uid, "sw_m1_owner_change_auto", "1")
        self.create_step(cursor, uid, m1, "M1", "05", context=None)
        m1 = self.Switching.browse(cursor, uid, m1.id, {"browse_reference": True})
        m105 = m1.step_ids[-1].pas_id
        m105.write({"data_activacio": context.get("data_activacio", "2021-08-05")})

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

            # activate contract
            self.Polissa.send_signal(cursor, uid, [contract_id], [
                'validar', 'contracte'
            ])

            m1 = self.get_m1_02_ct(
                txn, contract_id, "S", context={"data_activacio": "2016-08-15"})
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

            # activate contract
            self.Polissa.send_signal(cursor, uid, [contract_id], [
                'validar', 'contracte'
            ])

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

    def test_ff_collectiu_atr_m1_01_no_auto(self):
        sw_obj = self.openerp.pool.get("giscedata.switching")
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.switch(txn, "comer")

            # Create M1 01 no auto
            contract_id = self.get_contract_id(txn)

            self.change_polissa_comer(txn)
            self.update_polissa_distri(txn)
            self.activar_polissa_CUPS(txn, context={
                "polissa_xml_id": "polissa_0001"})

            step_id = self.create_case_and_step(
                cursor, uid, contract_id, "M1", "01"
            )
            m101 = step_obj.browse(cursor, uid, step_id)
            m1 = sw_obj.browse(cursor, uid, m101.sw_id.id)

            self.assertFalse(m1.collectiu_atr)

    def test_ff_collectiu_atr_m1_01_auto(self):
        sw_obj = self.openerp.pool.get("giscedata.switching")
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        partner_address_obj = self.openerp.pool.get('res.partner.address')

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            hist_autoconsum_id = self.IrModelData.get_object_reference(
                cursor, uid, 'giscedata_cups', 'rel_autoconsum_cups_tarifa_018_autoconsum_41'
            )[1]
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'base', 'res_partner_gisce')[1]
            partner_address_obj.create(cursor, uid, {'phone': 666999222, 'partner_id': partner_id})
            """m1_xml_path = get_module_resource(
                "giscedata_switching", "tests", "fixtures", "m102_new.xml"
            )
            with open(m1_xml_path, "r") as f:
                m1_xml = f.read()
            m1_xml = m1_xml.replace(
                "<Colectivo>201412111009",
                "<CodigoDeSolicitud>{0}".format(codi_sollicitud)
            )"""
            self.switch(txn, "comer")

            # Create M1 01 no auto
            contract_id = self.get_contract_id(txn)

            self.change_polissa_comer(txn)
            self.update_polissa_distri(txn)
            self.activar_polissa_CUPS(txn, context={
                "polissa_xml_id": "polissa_0001"})

            step_id = self.create_case_and_step(
                cursor, uid, contract_id, "M1", "01"
            )
            m101 = step_obj.browse(cursor, uid, step_id)
            datos_cau_obj = self.openerp.pool.get('giscedata.switching.datos.cau')
            datos_cau_ids = datos_cau_obj.dummy_create(
                cursor, uid, m101.sw_id, '04', hist_autoconsum_id)
            vals = {
                'dades_cau': datos_cau_ids,
                'change_type': 'tarpot',
                'tariff': '018',
                'phone_num': '666888555',
                'phone_pre': '034',
                'con_name': '0018_A41',
                'con_sur1': 'asdfg',
                'con_sur2': 'gfdsa',
                'power_p1': 4600,
                'power_p2': 4600,
                'power_p3': 4600,
                'power_invoicing': '1',
            }
            m101.config_step(vals)

            # No col·lectiu
            m1 = sw_obj.browse(cursor, uid, m101.sw_id.id)
            self.assertFalse(m1.collectiu_atr)

            # Col·lectiu
            datos_cau_obj.write(cursor, uid, datos_cau_ids, {'collectiu': True})
            m101.write({'dades_cau': datos_cau_ids})
            m1 = sw_obj.browse(cursor, uid, m101.sw_id.id)
            self.assertTrue(m1.collectiu_atr)

    def test_ff_collectiu_atr_m1_05_no_auto(self):
        sw_obj = self.openerp.pool.get("giscedata.switching")
        step_obj = self.openerp.pool.get("giscedata.switching.m1.01")
        partner_address_obj = self.openerp.pool.get('res.partner.address')

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            hist_autoconsum_id = self.IrModelData.get_object_reference(
                cursor, uid, 'giscedata_cups', 'rel_autoconsum_cups_tarifa_018_autoconsum_41'
            )[1]
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'base', 'res_partner_gisce')[1]
            partner_address_obj.create(cursor, uid, {'phone': 666999222, 'partner_id': partner_id})

            self.switch(txn, "comer")

            # Create M1 01 no auto
            contract_id = self.get_contract_id(txn)

            self.change_polissa_comer(txn)
            self.update_polissa_distri(txn)
            self.activar_polissa_CUPS(txn, context={
                "polissa_xml_id": "polissa_0001"})

            step_id = self.create_case_and_step(
                cursor, uid, contract_id, "M1", "01"
            )
            m101 = step_obj.browse(cursor, uid, step_id)
            datos_cau_obj = self.openerp.pool.get('giscedata.switching.datos.cau')
            datos_cau_ids = datos_cau_obj.dummy_create(
                cursor, uid, m101.sw_id, '04', hist_autoconsum_id)
            vals = {
                'dades_cau': datos_cau_ids,
                'change_type': 'tarpot',
                'tariff': '018',
                'phone_num': '666888555',
                'phone_pre': '034',
                'con_name': '0018_A41',
                'con_sur1': 'asdfg',
                'con_sur2': 'gfdsa',
                'power_p1': 4600,
                'power_p2': 4600,
                'power_p3': 4600,
                'power_invoicing': '1',
            }
            m101.config_step(vals)

            # No col·lectiu
            m1 = sw_obj.browse(cursor, uid, m101.sw_id.id)
            self.assertFalse(m1.collectiu_atr)

            # Carreguem el pas 02 de la distri
            m1_02_xml_path = get_module_resource(
                "giscedata_switching", "tests", "fixtures", "m102_new.xml"
            )
            with open(m1_02_xml_path, "r") as f:
                m1_02_xml = f.read()
            # codi_sollicitud = '20250605160800'
            m1_02_xml = m1_02_xml.replace(
                "<CodigoDeSolicitud>201412111009",
                "<CodigoDeSolicitud>{0}".format(m1.codi_sollicitud)
            )

            # Carreguem el pas 05 de la distri
            m1_05_xml_path = get_module_resource(
                "giscedata_switching", "tests", "fixtures", "m105_canvi_autoconsum.xml"
            )
            with open(m1_05_xml_path, "r") as f:
                m1_05_xml = f.read()
            m1_05_xml = m1_05_xml.replace(
                "<CodigoDeSolicitud>201607211260",
                "<CodigoDeSolicitud>{0}".format(m1.codi_sollicitud)
            )
            m1_05_xml = m1_05_xml.replace(
                "<CUPS>ES0021126262693495FV",
                "<CUPS>ES1234000000000001JN0F",
            )

            # Import XML
            sw_obj.importar_xml(
                cursor, uid, m1_02_xml, "m1_02.xml"
            )
            sw_obj.importar_xml(
                cursor, uid, m1_05_xml, "m1_05.xml"
            )

            # Comprovem que és Col·lectiu
            m1 = sw_obj.browse(cursor, uid, m101.sw_id.id)
            self.assertTrue(m1.collectiu_atr)
