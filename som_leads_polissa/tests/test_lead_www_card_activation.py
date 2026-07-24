# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import mock
from osv import osv

from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwCardActivation(BaseSomLeadWwwTest):
    def _get_existing_member_values(self):
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
            "code": member.partner_id.ref.replace("S", ""),
        }
        return values, member.partner_id.id

    def _card_vals(self, token="tok_lead_123", masked_number="**** **** **** 4242"):
        return {
            "creditcard_token": token,
            "creditcard_masked_number": masked_number,
            "creditcard_expiry_date": "12/30",
            "creditcard_cof_txnid": "cof_123",
        }

    def test_activate_lead_assigns_recurrent_card_payment(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"
        values.pop("iban")

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.add_payment_card_data(
            self.cursor, self.uid, result["lead_id"], self._card_vals()
        )

        www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        polissa = lead.polissa_id

        payment_type_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        payment_mode_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_mode_card_recurrent"
        )[1]

        self.assertEqual(polissa.tipo_pago.id, payment_type_id)
        self.assertEqual(polissa.payment_mode_id.id, payment_mode_id)
        self.assertTrue(polissa.creditcard)
        self.assertEqual(polissa.creditcard.partner_id.id, polissa.pagador.id)
        self.assertEqual(polissa.creditcard.token, "tok_lead_123")
        self.assertEqual(polissa.creditcard.masked_number, "**** **** **** 4242")
        self.assertEqual(polissa.creditcard.expiry_date, "12/30")
        self.assertEqual(polissa.creditcard.cof_txnid, "cof_123")

    def test_create_lead_does_not_mark_error_when_only_card_data_is_missing(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"
        values.pop("iban")

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        received_stage_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_recieved"
        )[1]

        self.assertFalse(result["error"])
        self.assertEqual(lead.crm_id.state, 'open')
        self.assertEqual(lead.crm_id.stage_id.id, received_stage_id)

        with self.assertRaises(osv.except_osv):
            www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])

    def test_add_payment_card_data_allows_activation_after_missing_card_data(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"
        values.pop("iban")

        result = www_lead_o.create_lead(self.cursor, self.uid, values)

        card_result = www_lead_o.add_payment_card_data(
            self.cursor, self.uid, result["lead_id"], self._card_vals()
        )

        self.assertEqual(card_result["lead_id"], result["lead_id"])
        self.assertFalse(card_result["error"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.crm_id.state, 'open')

        www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertTrue(lead.polissa_id)

    def test_create_lead_uses_temporary_card_data_during_validation(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"
        values.pop("iban")

        captured = {}
        original_method = lead_o._get_card_payment_polissa_values

        def _wrapped_get_card_payment_polissa_values(cursor, uid, lead, pagador_id, context=None):
            captured["token"] = lead.creditcard_token
            return original_method(cursor, uid, lead, pagador_id, context=context)

        with mock.patch.object(
            lead_o,
            "_get_card_payment_polissa_values",
            side_effect=_wrapped_get_card_payment_polissa_values,
        ):
            result = www_lead_o.create_lead(self.cursor, self.uid, values)

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertFalse(result["error"])
        self.assertEqual(captured["token"], "validation-token-{}".format(result["lead_id"]))
        self.assertFalse(lead.creditcard_token)

    def test_activate_lead_reuses_existing_card_with_same_token_and_data(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        card_o = self.get_model("res.partner.creditcard")

        values, partner_id = self._get_existing_member_values()
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"
        values.pop("iban")

        existing_card_id = card_o.create(
            self.cursor,
            self.uid,
            {
                "partner_id": partner_id,
                "token": "tok_existing_member",
                "masked_number": "**** **** **** 1111",
                "expiry_date": "12/30",
                "cof_txnid": "cof_existing",
            },
        )

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.add_payment_card_data(
            self.cursor,
            self.uid,
            result["lead_id"],
            self._card_vals(token="tok_existing_member", masked_number="**** **** **** 1111"),
        )

        www_lead_o.activate_lead_sync(
            self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.polissa_id.creditcard.id, existing_card_id)

    def test_activate_lead_fails_when_existing_token_data_does_not_match(self):
        www_lead_o = self.get_model("som.lead.www")
        card_o = self.get_model("res.partner.creditcard")

        values, partner_id = self._get_existing_member_values()
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"

        card_o.create(
            self.cursor,
            self.uid,
            {
                "partner_id": partner_id,
                "token": "tok_existing_member",
                "masked_number": "**** **** **** 9999",
                "expiry_date": "12/30",
                "cof_txnid": "cof_existing",
            },
        )

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.add_payment_card_data(
            self.cursor,
            self.uid,
            result["lead_id"],
            self._card_vals(token="tok_existing_member", masked_number="**** **** **** 1111"),
        )

        with self.assertRaises(osv.except_osv):
            www_lead_o.activate_lead_sync(self.cursor, self.uid, result["lead_id"])
