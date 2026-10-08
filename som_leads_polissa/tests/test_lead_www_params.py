# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwParams(BaseSomLeadWwwTest):
    def _webforms_user_id(self):
        return self.get_model("ir.model.data").get_object_reference(
            self.cursor,
            self.uid,
            "base_extended_som",
            "res_users_webforms",
        )[1]

    def _campaign_root_ids(self):
        ir_model_o = self.get_model("ir.model.data")
        partner_root_id = ir_model_o.get_object_reference(
            self.cursor,
            self.uid,
            "som_leads_polissa",
            "res_partner_category_campaigns",
        )[1]
        polissa_root_id = ir_model_o.get_object_reference(
            self.cursor,
            self.uid,
            "som_leads_polissa",
            "giscedata_polissa_category_campaigns",
        )[1]
        return partner_root_id, polissa_root_id

    def test_create_lead_without_params_keeps_webforms_owner(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.crm_id.user_id.id, self._webforms_user_id())
        self.assertFalse(lead.lead_tag)

    def test_create_lead_assigns_owner_by_login(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        user_o = self.get_model("res.users")
        owner_login = user_o.read(
            self.cursor, self.uid, self.uid, ["login"]
        )["login"]
        self._basic_values["params"] = {"owner": owner_login}

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.crm_id.user_id.id, self.uid)

    def test_unknown_owner_keeps_webforms_owner(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        self._basic_values["params"] = {"owner": "missing-webform-owner"}

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.crm_id.user_id.id, self._webforms_user_id())

    def test_send_email_param_is_only_stored_in_history(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        self._basic_values["params"] = {"send_email": True}

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        history = "\n".join(
            line.description or "" for line in lead.history_line
        )

        self.assertIn("send_email: true", history)

    def test_lead_tag_creates_and_assigns_campaign_categories(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_category_o = self.get_model("res.partner.category")
        polissa_category_o = self.get_model("giscedata.polissa.category")
        partner_root_id, polissa_root_id = self._campaign_root_ids()
        lead_tag = "Campanya Test"
        self._basic_values["params"] = {"lead_tag": lead_tag}

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.lead_tag, lead_tag)

        www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        partner_category_ids = partner_category_o.search(
            self.cursor,
            self.uid,
            [("name", "=", lead_tag), ("parent_id", "=", partner_root_id)],
        )
        polissa_category_ids = polissa_category_o.search(
            self.cursor,
            self.uid,
            [("name", "=", lead_tag), ("parent_id", "=", polissa_root_id)],
        )
        self.assertEqual(len(partner_category_ids), 1)
        self.assertEqual(len(polissa_category_ids), 1)
        self.assertIn(
            partner_category_ids[0], [category.id for category in lead.partner_id.category_id]
        )
        self.assertIn(
            polissa_category_ids[0], [category.id for category in lead.polissa_id.category_id]
        )

    def test_lead_tag_reuses_existing_campaign_categories(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_category_o = self.get_model("res.partner.category")
        polissa_category_o = self.get_model("giscedata.polissa.category")
        partner_root_id, polissa_root_id = self._campaign_root_ids()
        lead_tag = "Campanya Existent"
        partner_category_id = partner_category_o.create(
            self.cursor,
            self.uid,
            {"name": lead_tag, "parent_id": partner_root_id},
        )
        polissa_category_id = polissa_category_o.create(
            self.cursor,
            self.uid,
            {"name": lead_tag, "parent_id": polissa_root_id},
        )
        self._basic_values["params"] = {"lead_tag": lead_tag}

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertIn(
            partner_category_id, [category.id for category in lead.partner_id.category_id]
        )
        self.assertIn(
            polissa_category_id, [category.id for category in lead.polissa_id.category_id]
        )
        self.assertEqual(
            partner_category_o.search_count(
                self.cursor,
                self.uid,
                [("name", "=", lead_tag), ("parent_id", "=", partner_root_id)],
            ),
            1,
        )
        self.assertEqual(
            polissa_category_o.search_count(
                self.cursor,
                self.uid,
                [("name", "=", lead_tag), ("parent_id", "=", polissa_root_id)],
            ),
            1,
        )

    def test_lead_tag_does_not_modify_an_existing_partner(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")
        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        original_category_ids = set(
            category.id for category in member.partner_id.category_id
        )
        vat = member.partner_id.vat.replace("ES", "")
        del self._basic_values["new_member_info"]
        self._basic_values.update({
            "linked_member": "already_member",
            "linked_member_info": {
                "vat": vat,
                "code": member.partner_id.ref.replace("S", ""),
            },
            "params": {"lead_tag": "Campanya Partner Existent"},
        })

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(
            set(category.id for category in lead.partner_id.category_id),
            original_category_ids,
        )
        self.assertIn(
            "Campanya Partner Existent",
            [category.name for category in lead.polissa_id.category_id],
        )
