# -*- coding: utf-8 -*-

from destral import testing
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
        }

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
