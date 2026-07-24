# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from osv import osv

from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwValidation(BaseSomLeadWwwTest):
    def test_create_lead_crm_stages_and_section(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        webform_stage_recieved_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_recieved"
        )[1]

        webform_stage_converted_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_converted"
        )[1]

        webform_stage_error_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_error"
        )[1]

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_recieved_id)
        self.assertEqual(lead.crm_id.state, 'open')

        # we need to reload the browse record because the cache
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_converted_id)
        self.assertEqual(lead.crm_id.state, 'done')

        # Test the error stage (cant have 2 leads on the same cups)
        values = self._basic_values
        values["new_member_info"]["vat"] = "53247948G"
        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertTrue(result["error"])
        self.assertEqual(lead.crm_id.state, 'pending')
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_error_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_bad_linked_member_fails(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["linked_member"] = "Nye he he he he"

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_bad_member_vat_number_data_fails(self):
        www_lead_o = self.get_model("som.lead.www")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        del values["new_member_info"]
        values["linked_member"] = "already_member"
        values["linked_member_info"] = {
            "vat": vat,
            "code": "S000042",  # Just a random different code
        }

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_existing_new_member_vat_fails(self):
        www_lead_o = self.get_model("som.lead.www")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        values["new_member_info"]["vat"] = vat

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_cnae_random_contract_not_created(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]["cnae"] = "123456789"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.cnae, None)
        self.assertIn("cnae: '123456789'", lead.history_line[1].description)

        with self.assertRaises(osv.except_osv) as e:
            www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])
        self.assertIn("CNAE", e.exception.value)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()
