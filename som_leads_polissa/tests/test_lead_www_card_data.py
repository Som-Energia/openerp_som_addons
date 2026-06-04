# -*- encoding: utf-8 -*-
from __future__ import absolute_import

import mock
from osv import osv

from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwCardData(BaseSomLeadWwwTest):
    def test_add_payment_card_data_stores_credit_card_fields(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["member_payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)

        card_result = www_lead_o.add_payment_card_data(
            self.cursor,
            self.uid,
            result["lead_id"],
            {
                "token": "tok_lead_123",
                "masked_number": "**** **** **** 4242",
                "expiry_date": "12/30",
                "cof_txnid": "cof_123",
            },
        )

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(card_result["lead_id"], result["lead_id"])
        self.assertFalse(card_result["error"])
        self.assertEqual(lead.creditcard_token, "tok_lead_123")
        self.assertEqual(lead.creditcard_masked_number, "**** **** **** 4242")
        self.assertEqual(lead.creditcard_expiry_date, "12/30")
        self.assertEqual(lead.creditcard_cof_txnid, "cof_123")

    def test_add_payment_card_data_returns_revalidation_error_when_lead_remains_blocked(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["member_payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        error_info = {"code": "Unactivable", "error": "still blocked", "trace": []}

        with mock.patch.object(
            www_lead_o, "_check_lead_can_be_activated", return_value=error_info
        ):
            card_result = www_lead_o.add_payment_card_data(
                self.cursor,
                self.uid,
                result["lead_id"],
                {
                    "token": "tok_lead_123",
                    "masked_number": "**** **** **** 4242",
                    "expiry_date": "12/30",
                    "cof_txnid": "cof_123",
                },
            )

        error_stage_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_error"
        )[1]
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(card_result["lead_id"], result["lead_id"])
        self.assertEqual(card_result["error"], error_info)
        self.assertEqual(lead.crm_id.state, 'pending')
        self.assertEqual(lead.crm_id.stage_id.id, error_stage_id)

    def test_add_payment_card_data_fails_for_non_card_recurrent_method(self):
        www_lead_o = self.get_model("som.lead.www")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)

        with self.assertRaises(osv.except_osv):
            www_lead_o.add_payment_card_data(
                self.cursor,
                self.uid,
                result["lead_id"],
                {
                    "token": "tok_lead_123",
                    "masked_number": "**** **** **** 4242",
                    "expiry_date": "12/30",
                    "cof_txnid": "cof_123",
                },
            )

    def test_add_payment_card_data_fails_when_card_already_defined(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["member_payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)

        card_vals = {
            "token": "tok_lead_123",
            "masked_number": "**** **** **** 4242",
            "expiry_date": "12/30",
            "cof_txnid": "cof_123",
        }

        www_lead_o.add_payment_card_data(
            self.cursor, self.uid, result["lead_id"], card_vals
        )

        with self.assertRaises(osv.except_osv):
            www_lead_o.add_payment_card_data(
                self.cursor, self.uid, result["lead_id"], card_vals
            )

    def test_add_payment_card_data_fails_when_lead_is_already_activated(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["member_payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.add_payment_card_data(
            self.cursor,
            self.uid,
            result["lead_id"],
            {
                "token": "tok_lead_123",
                "masked_number": "**** **** **** 4242",
                "expiry_date": "12/30",
                "cof_txnid": "cof_123",
            },
        )
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        with self.assertRaises(osv.except_osv):
            www_lead_o.add_payment_card_data(
                self.cursor,
                self.uid,
                result["lead_id"],
                {
                    "token": "tok_lead_123",
                    "masked_number": "**** **** **** 4242",
                    "expiry_date": "12/30",
                    "cof_txnid": "cof_123",
                },
            )

    def test_add_payment_card_data_requires_all_card_fields(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["member_payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)

        with self.assertRaises(osv.except_osv):
            www_lead_o.add_payment_card_data(
                self.cursor,
                self.uid,
                result["lead_id"],
                {
                    "token": "tok_lead_123",
                    "masked_number": "**** **** **** 4242",
                    "expiry_date": "12/30",
                },
            )
