# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import os
import base64
from datetime import datetime

from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwCreation(BaseSomLeadWwwTest):
    def test_create_lead_sets_default_billing_payment_method(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.billing_payment_method, "remesa")

    def test_create_lead_keeps_explicit_billing_payment_method(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["billing_payment_method"] = "card_recurrent"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.billing_payment_method, "card_recurrent")

    def test_create_simple_domestic_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        sw_o = self.get_model("giscedata.switching")
        ir_model_o = self.get_model("ir.model.data")
        mailbox_o = self.get_model('poweremail.mailbox')

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        self.assertFalse(result["error"])

        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.name, "40323835M / ES0177000000000000LR")

        # Check that the lead has a valid member number and is the same as the titular
        self.assertTrue(lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref, lead.member_number)

        # Check the member category
        member_category_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_partner_account", "res_partner_category_soci"
        )[1]
        self.assertIn(member_category_id, [c.id for c in lead.polissa_id.soci.category_id])

        # Check that the contract has the member field filled correctly
        self.assertEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        # Check the invoicing mode
        self.assertEqual(lead.polissa_id.facturacio_potencia, "icp")

        # Check that the ATR is created with C1 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C1"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])
        self.assertEqual(atr_case.state, "draft")

        # check default 'contratacion_incondicional_bs'
        c1 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(c1.contratacion_incondicional_bs, "N")

        # Check the pricelist and mode facturacio
        peninsular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        )[1]
        self.assertEqual(lead.polissa_id.llista_preu.id, peninsular_pricelist_id)
        self.assertEqual(lead.polissa_id.mode_facturacio, 'atr')

        # Check that don't have self consumption
        self.assertEqual(lead.polissa_id.autoconsumo, '00')

        # Check the tension (default is 230)
        tensio_230 = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'giscedata_tensions', 'tensio_230')[1]
        self.assertEqual(lead.polissa_id.tensio_normalitzada.id, tensio_230)

        # Check if user_id ("comercial") is created on polissa
        webforms_user_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_users_webforms"
        )[1]
        self.assertEqual(lead.polissa_id.user_id.id, webforms_user_id)

        # Check that the address is correcty created
        self.assertEqual(
            lead.polissa_id.direccio_notificacio.street,
            "Carrer Falsa, 123 BLQ. B ESC. A 5 C"
        )

        # Check the catastral reference
        self.assertEqual(lead.polissa_id.cups.ref_catastral, "9872023VH5797S0001WX")

        # Check that the mail was sent
        template_name = "email_contracte_esborrany_nou_soci"
        template_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', template_name)[1]
        mails = mailbox_o.search(
            self.cursor, self.uid, [
                ("template_id", "=", template_id),
                ("folder", "=", "outbox"),
            ]
        )
        self.assertEqual(len(mails), 1)

        # Check partner lang and member date
        self.assertEqual(lead.partner_id.lang, "es_ES")
        self.assertEqual(lead.partner_id.date, datetime.today().strftime("%Y-%m-%d"))
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_domestic_lead_indexada(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["contract_info"]["is_indexed"] = True
        values["contract_info"]["indexed_contract_terms_accepted"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        peninsular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_peninsula_2024"
        )[1]
        self.assertEqual(lead.polissa_id.llista_preu.id, peninsular_pricelist_id)
        self.assertEqual(lead.polissa_id.mode_facturacio, 'index')
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_juridic_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")

        values = self._basic_values
        values["new_member_info"]["is_juridic"] = True
        values["new_member_info"]["vat"] = "C81837452"
        values["new_member_info"]["name"] = "PEC COOP SCCL"
        values["new_member_info"]["proxy_name"] = "Pepito Palotes"
        values["new_member_info"]["proxy_vat"] = "40323835M"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.is_new_contact, True)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.name, "C81837452 / ES0177000000000000LR")

        # Check that the representative is created and correctly linked
        rep_id = partner_o.search(self.cursor, self.uid, [("vat", "=", "ES40323835M")])[0]
        self.assertEqual(lead.polissa_id.titular.representante_id.id, rep_id)
        self.assertEqual(lead.polissa_id.titular.name, "PEC COOP SCCL")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_juridic_lead_with_existing_representative(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")
        imd_o = self.get_model('ir.model.data')

        existing_partner_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'base', 'res_partner_agrolait'
        )[1]

        existing_partner_vat = partner_o.read(
            self.cursor, self.uid, existing_partner_id, ['vat']
        )['vat']

        values = self._basic_values
        values["new_member_info"]["is_juridic"] = True
        values["new_member_info"]["vat"] = "C81837452"
        values["new_member_info"]["name"] = "PEC COOP SCCL"
        values["new_member_info"]["proxy_name"] = "Pepito Palotes"
        values["new_member_info"]["proxy_vat"] = existing_partner_vat

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that no new partner is created
        num_repeated_vats = len(
            partner_o.search(self.cursor, self.uid, [("vat", "=", existing_partner_vat)]))
        self.assertEqual(num_repeated_vats, 1)

        # Check that the representative is correctly linked
        self.assertEqual(lead.polissa_id.titular.representante_id.id, existing_partner_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_30TD(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]["tariff"] = "3.0TD"
        values["contract_info"]["powers"] = ["4400", "4900", "5000", "6000", "7000", "15001"]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(len(lead.polissa_id.potencies_periode), 6)
        self.assertEqual(lead.polissa_id.tarifa.name, "3.0TD")
        self.assertEqual(lead.polissa_id.facturacio_potencia, "max")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_donatiu(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["donation"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertIs(lead.polissa_id.donatiu, True)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_owner_change_C2_20TD(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = 'C2'

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the ATR is created with C2 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C2"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])
        self.assertEqual(atr_case.state, "draft")

        # check change type owner
        c2 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(c2.sollicitudadm, "S")
        self.assertEqual(c2.canvi_titular, "T")
        self.assertEqual(c2.control_potencia, "1")

        # check default 'contratacion_incondicional_bs'
        self.assertEqual(c2.contratacion_incondicional_bs, "S")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_owner_change_C2_30TD(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = "C2"
        values["contract_info"]["tariff"] = "3.0TD"
        values["contract_info"]["powers"] = ["4400", "4900", "5000", "6000", "7000", "15001"]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the ATR is created with C2 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C2"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])
        self.assertEqual(atr_case.state, "draft")

        # check change type owner
        c2 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(c2.sollicitudadm, "S")
        self.assertEqual(c2.canvi_titular, "T")
        self.assertEqual(c2.control_potencia, "2")

        # check default contratacion_incondicional_bs
        self.assertEqual(c2.contratacion_incondicional_bs, "S")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_new_cups_A3(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = 'A3'

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the ATR is created with A3 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "A3"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])

        a3 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(a3.control_potencia, "1")
        self.assertEqual(atr_case.state, "draft")
        self.assertEqual(a3.cnae.name, values["contract_info"]["cnae"])
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_from_canarias(self):
        ir_model_o = self.get_model("ir.model.data")
        cfg_o = self.get_model("res.config")
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values

        laguna_municipi_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_38023"
        )[1]
        tenerife_state_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "l10n_ES_toponyms", "ES38"
        )[1]

        values["contract_info"]["cups_address"]["city_id"] = laguna_municipi_id
        values["contract_info"]["cups_address"]["state_id"] = tenerife_state_id
        values["contract_info"]["cups"] = "ES0031601267738003JC0F"

        canarian_posicio_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "fp_canarias_vivienda"
        )[1]
        cfg_o.set(self.cursor, self.uid, "fp_canarias_vivienda_id", canarian_posicio_id)

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        insular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]

        self.assertEqual(lead.polissa_id.fiscal_position_id.id, canarian_posicio_id)
        self.assertEqual(lead.polissa_id.llista_preu.id, insular_pricelist_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_from_balears(self):
        ir_model_o = self.get_model("ir.model.data")
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values

        capdepera_municipi_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_07014"
        )[1]
        balears_state_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "l10n_ES_toponyms", "ES07"
        )[1]

        values["contract_info"]["cups_address"]["city_id"] = capdepera_municipi_id
        values["contract_info"]["cups_address"]["state_id"] = balears_state_id

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        insular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]

        self.assertEqual(lead.polissa_id.llista_preu.id, insular_pricelist_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_add_attachments_to_simple_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")
        ir_attach_o = self.get_model("ir.attachment")

        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'assets', 'blank.pdf'), 'rb') as pdf_file:
            pdf_data = pdf_file.read()

        encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

        values = self._basic_values

        values["attachments"] = [
            {
                "filename": "blank.pdf",
                "datas": encoded_pdf,
                "category": "lead_old_invoice"
            }
        ]

        old_invoice_categ_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "ir_attachment_lead_old_invoice"
        )[1]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        search_params = [
            ("res_model", "=", "giscedata.polissa"),
            ("res_id", "=", lead.polissa_id.id),
            ("category_id", "=", old_invoice_categ_id)
        ]

        ir_attach_ids = ir_attach_o.search(self.cursor, self.uid, search_params)

        self.assertEqual(len(ir_attach_ids), 1)

        # check that the attachment data is not stored in the log
        self.assertNotIn("datas:", lead.polissa_id.observacions)

        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()
