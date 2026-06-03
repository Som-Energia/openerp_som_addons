# -*- encoding: utf-8 -*-
from __future__ import absolute_import


from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwMisc(BaseSomLeadWwwTest):
    def test_www_form_data_and_create_entites_log_is_stored(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertIn("name: Pepito", lead.polissa_id.observacions)

        # we check the second line because the first has the stage change
        self.assertIn("ES40323835M", lead.history_line[1].description)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_lead_with_demographic_data(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["new_member_info"]["gender"] = "non_binary"
        values["new_member_info"]["birthdate"] = "1990-01-01"
        values["new_member_info"]["referral_source"] = "opcions"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.polissa_id.titular.gender, "non_binary")
        self.assertEqual(lead.polissa_id.titular.birthdate, "1990-01-01")
        self.assertEqual(lead.polissa_id.titular.referral_source, "opcions")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_comercial_info_accepted_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["new_member_info"]["is_juridic"] = True
        values["new_member_info"]["vat"] = "C81837452"
        values["new_member_info"]["name"] = "PEC COOP SCCL"
        values["new_member_info"]["proxy_name"] = "Pepito Palotes"
        values["new_member_info"]["proxy_vat"] = "40323835M"
        values["new_member_info"]["comercial_info_accepted"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.comercial_info_accepted, True)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_trifasic_tension(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["contract_info"]["phase"] = "3x230/400"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        tensio_trifasica = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'giscedata_tensions', 'tensio_3x230_400')[1]
        self.assertEqual(lead.polissa_id.tensio_normalitzada.id, tensio_trifasica)

    def test_lead_with_phone_without_prefix_dont_fail(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["new_member_info"]["phone"] = "612345678"

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        self.assertFalse(result["error"])

        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the phone and prefix are correctly set
        self.assertEqual(lead.titular_phone, "612345678")
        self.assertEqual(lead.titular_phone_prefix, False)

        # +34 is the default value in the res.partner.address
        self.assertEqual(lead.polissa_id.direccio_notificacio.phone, "612345678")
        self.assertEqual(lead.polissa_id.direccio_notificacio.phone_prefix.name, "+34")

    def test_new_lead_with_phone_prefix(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["new_member_info"]["phone"] = "+850 612345678"

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        self.assertFalse(result["error"])

        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the phone and prefix are correctly set
        self.assertEqual(lead.titular_phone, "612345678")
        self.assertEqual(lead.titular_phone_prefix.name, "+850")

        self.assertEqual(lead.polissa_id.direccio_notificacio.phone, "612345678")
        self.assertEqual(lead.polissa_id.direccio_notificacio.phone_prefix.name, "+850")

    def test_already_member_lead_with_phone_prefix(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")
        partner_o = self.get_model("res.partner")
        address_o = self.get_model("res.partner.address")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        partner_o.write(self.cursor, self.uid, member.partner_id.id, {'lang': 'ca_ES'})

        vat = member.partner_id.vat.replace("ES", "")

        # +34 is the default so we only change the phone
        address_o.write(
            self.cursor, self.uid, member.partner_id.address[0].id, {'phone': "612345678"})

        values = self._basic_values
        del values["new_member_info"]
        values["linked_member"] = "already_member"
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the phone and prefix are correctly set
        self.assertEqual(lead.titular_phone, "612345678")
        self.assertEqual(lead.titular_phone_prefix.name, "+34")

        # Change the phone and assert that it arrives correctly to the address
        new_prefix_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_850")[1]
        lead_o.write(self.cursor, self.uid, lead.id, {
            "titular_phone": "699999999",
            "titular_phone_prefix": new_prefix_id,
        })
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.polissa_id.direccio_notificacio.phone, "699999999")
        self.assertEqual(lead.polissa_id.direccio_notificacio.phone_prefix.name, "+850")

    def test_create_lead_with_andorra_phone(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["new_member_info"]["phone"] = "+376 123456"

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        self.assertFalse(result["error"])

        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the phone and prefix are correctly set
        self.assertEqual(lead.titular_phone, "123456")
        self.assertEqual(lead.titular_phone_prefix.name, "+376")

        self.assertEqual(lead.polissa_id.direccio_notificacio.phone, "123456")
        self.assertEqual(lead.polissa_id.direccio_notificacio.phone_prefix.name, "+376")
