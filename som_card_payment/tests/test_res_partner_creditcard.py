# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from osv import osv
from osv.orm import FieldsValidationException


class TestResPartnerCreditCard(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestResPartnerCreditCard, self).setUp()
        self.partner_obj = self.openerp.pool.get("res.partner")
        self.creditcard_obj = self.openerp.pool.get("res.partner.creditcard")
        self.partner_id = self.partner_obj.create(
            self.cursor,
            self.uid,
            {"name": "Partner test card payment"},
        )

    def _base_vals(self):
        return {
            "partner_id": self.partner_id,
            "token": "tok_test_123",
            "masked_number": "**** **** **** 1234",
            "expiry_date": "12/34",
            "cof_txnid": "cof_test_123",
        }

    def _resolve(self, card_data=None, partner_id=None):
        card_data = card_data or self._base_vals()
        card_data = card_data.copy()
        card_data.pop("partner_id", None)
        return self.creditcard_obj.resolve_for_payer(
            self.cursor,
            self.uid,
            partner_id or self.partner_id,
            card_data,
        )

    def test_resolve_for_payer_reuses_compatible_card(self):
        card_id = self.creditcard_obj.create(
            self.cursor, self.uid, self._base_vals()
        )

        result = self._resolve()

        self.assertEqual(result, {"id": card_id, "disposition": "reused"})
        card_ids = self.creditcard_obj.search(
            self.cursor, self.uid, [("token", "=", "tok_test_123")]
        )
        self.assertEqual(card_ids, [card_id])

    def test_resolve_for_payer_creates_exactly_one_owned_card(self):
        result = self._resolve()

        card = self.creditcard_obj.read(
            self.cursor,
            self.uid,
            result["id"],
            ["partner_id", "token", "masked_number", "expiry_date", "cof_txnid"],
        )
        self.assertEqual(result["disposition"], "created")
        self.assertEqual(card["partner_id"][0], self.partner_id)
        self.assertEqual(card["token"], "tok_test_123")
        self.assertEqual(card["cof_txnid"], "cof_test_123")
        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", "tok_test_123")]
            ),
            [result["id"]],
        )

    def test_resolve_for_payer_rejects_token_metadata_conflict(self):
        card_id = self.creditcard_obj.create(
            self.cursor, self.uid, self._base_vals()
        )
        conflicting_data = self._base_vals()
        conflicting_data["masked_number"] = "**** **** **** 9999"

        with self.assertRaises(osv.except_osv):
            self._resolve(conflicting_data)

        card = self.creditcard_obj.read(
            self.cursor, self.uid, card_id, ["masked_number"]
        )
        self.assertEqual(card["masked_number"], "**** **** **** 1234")

    def test_resolve_for_payer_rejects_token_owned_by_another_payer(self):
        self.creditcard_obj.create(self.cursor, self.uid, self._base_vals())
        other_partner_id = self.partner_obj.create(
            self.cursor, self.uid, {"name": "Other card payer"}
        )

        with self.assertRaises(osv.except_osv):
            self._resolve(partner_id=other_partner_id)

        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", "tok_test_123")]
            ),
            self.creditcard_obj.search(
                self.cursor,
                self.uid,
                [("token", "=", "tok_test_123"), ("partner_id", "=", self.partner_id)],
            ),
        )

    def test_check_expiry_date_accepts_valid_format(self):
        vals = self._base_vals()
        vals["expiry_date"] = "12/34"

        card_id = self.creditcard_obj.create(self.cursor, self.uid, vals)
        self.assertTrue(card_id)

    def test_check_expiry_date_rejects_invalid_month(self):
        vals = self._base_vals()
        vals["expiry_date"] = "13/24"

        with self.assertRaises(FieldsValidationException):
            self.creditcard_obj.create(self.cursor, self.uid, vals)

    def test_check_expiry_date_rejects_invalid_write_format(self):
        vals = self._base_vals()
        vals["expiry_date"] = "01/24"
        card_id = self.creditcard_obj.create(self.cursor, self.uid, vals)

        with self.assertRaises(FieldsValidationException):
            self.creditcard_obj.write(
                self.cursor,
                self.uid,
                [card_id],
                {"expiry_date": "1/24"},
            )

    def test_create_accepts_different_tokens(self):
        vals_1 = self._base_vals()
        vals_1["token"] = "tok_unique_1"
        vals_2 = self._base_vals()
        vals_2["token"] = "tok_unique_2"

        card_id_1 = self.creditcard_obj.create(self.cursor, self.uid, vals_1)
        card_id_2 = self.creditcard_obj.create(self.cursor, self.uid, vals_2)

        self.assertTrue(card_id_1)
        self.assertTrue(card_id_2)
