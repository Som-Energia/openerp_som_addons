# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from osv import osv

from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwMemberLinking(BaseSomLeadWwwTest):
    def test_create_simple_domestic_lead_already_member(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")
        mailbox_o = self.get_model('poweremail.mailbox')
        partner_o = self.get_model("res.partner")
        address_o = self.get_model("res.partner.address")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        partner_o.write(self.cursor, self.uid, member.partner_id.id, {'lang': 'ca_ES'})

        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        del values["new_member_info"]
        values["linked_member"] = "already_member"
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.name, "{} / ES0177000000000000LR".format(vat,))

        self.assertEqual(member.partner_id.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        self.assertEqual(
            lead.polissa_id.direccio_notificacio.street,
            "Major, 32"
        )

        self.assertEqual(
            address_o.search_count(self.cursor, self.uid, [
                ('partner_id', '=', member.partner_id.id)
            ]), 1
        )

        template_name = "email_contracte_esborrany"
        template_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', template_name)[1]
        mails = mailbox_o.search(
            self.cursor, self.uid, [
                ("template_id", "=", template_id),
                ("folder", "=", "outbox"),
            ]
        )
        self.assertEqual(len(mails), 1)

        self.assertEqual(lead.partner_id.lang, "ca_ES")

    def test_create_simple_domestic_lead_sponsored(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")
        mailbox_o = self.get_model('poweremail.mailbox')

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        values["linked_member"] = "sponsored"
        values["contract_owner"] = values.pop("new_member_info")
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.name, "40323835M / ES0177000000000000LR")

        self.assertEqual(member.partner_id.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref[0], "T")
        self.assertNotEqual(lead.polissa_id.titular.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.soci.id, member.partner_id.id)
        self.assertNotEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        template_name = "email_contracte_esborrany"
        template_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', template_name)[1]
        mails = mailbox_o.search(
            self.cursor, self.uid, [
                ("template_id", "=", template_id),
                ("folder", "=", "outbox"),
            ]
        )
        self.assertEqual(len(mails), 1)
        self.mock_subscribe_customer.assert_called()

    def test_existing_customer_converts_as_member(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")
        ir_model_o = self.get_model("ir.model.data")
        pol_o = self.get_model("giscedata.polissa")
        member_o = self.get_model("somenergia.soci")

        gisce_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_gisce"
        )[1]
        agrolait_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_agrolait"
        )[1]
        gisce_contract = ir_model_o.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_gisce"
        )[1]
        pol_o.write(self.cursor, self.uid, [gisce_contract], {"soci": agrolait_id})
        partner_o.write(self.cursor, self.uid, [gisce_id], {"ref": "P000042"})
        gisce_br = partner_o.browse(self.cursor, self.uid, gisce_id)
        vat = gisce_br.vat.replace("ES", "")

        values = self._basic_values
        values["new_member_info"]["vat"] = vat

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.is_new_contact, False)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        gisce_br = partner_o.browse(self.cursor, self.uid, gisce_id)
        contract_member_id = pol_o.read(
            self.cursor, self.uid, gisce_contract, ['soci'])['soci'][0]
        member_category_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_partner_account", "res_partner_category_soci"
        )[1]

        self.assertEqual(gisce_br.ref[0], "S")
        self.assertIn(member_category_id, [c.id for c in gisce_br.category_id])
        self.assertEqual(contract_member_id, gisce_id)

        member_ids = member_o.search(
            self.cursor, self.uid, [("partner_id", "=", gisce_id)]
        )
        self.assertEqual(len(member_ids), 1)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_manual_member_number_error(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")
        member_o = self.get_model("somenergia.soci")
        values = self._basic_values
        values["linked_member"] = "sponsored"
        values["contract_owner"] = values.pop("new_member_info")
        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)["lead_id"]
        lead_o.write(
            self.cursor, self.uid, lead_id, {"member_number": "WRONGCODE", "titular_number": ""}
        )

        with self.assertRaises(osv.except_osv):
            lead_o.create_entities(self.cursor, self.uid, lead_id)

    def test_create_lead_with_existing_poblacio(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")
        address_o = self.get_model("res.partner.address")
        imd_o = self.get_model('ir.model.data')

        existing_partner_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', 'res_partner_nosoci1'
        )[1]
        existing_partner_vat = partner_o.read(
            self.cursor, self.uid, existing_partner_id, ['vat']
        )['vat']
        existing_address_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', 'res_partner_address_nosoci1'
        )[1]
        test_poblacio_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'base_extended', 'poble_01'
        )[1]
        test_municipi_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'base_extended', 'ine_01001'
        )[1]
        girona_municipi_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'base_extended', 'ine_17079'
        )[1]
        address_o.write(
            self.cursor, self.uid, existing_address_id, {
                'id_poblacio': test_poblacio_id,
                'id_municipi': test_municipi_id,
            }
        )

        values = self._basic_values
        values["new_member_info"]["address"]["city_id"] = girona_municipi_id
        values["new_member_info"]["vat"] = existing_partner_vat.replace("ES", "")

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.polissa_id.direccio_notificacio.id_municipi.id, girona_municipi_id)
        self.assertFalse(lead.polissa_id.direccio_notificacio.id_poblacio)

    def test_create_lead_with_existing_surnames(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")
        imd_o = self.get_model('ir.model.data')

        existing_partner_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', 'res_partner_nosoci1'
        )[1]
        existing_partner_vat = partner_o.read(
            self.cursor, self.uid, existing_partner_id, ['vat']
        )['vat']
        partner_o.write(
            self.cursor, self.uid, existing_partner_id, {
                'name': 'Cognom1 Cognom2, Nom'
            }
        )

        values = self._basic_values
        values["new_member_info"]["name"] = 'Nom'
        values["new_member_info"]["surname"] = 'Cognom1 Cognom2'
        values["new_member_info"]["vat"] = existing_partner_vat.replace("ES", "")

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.polissa_id.titular.name, 'Cognom1 Cognom2, Nom')
        self.assertEqual(lead.polissa_id.direccio_notificacio.name, 'Cognom1 Cognom2, Nom')
