# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from ctx import current_session, _context_stack
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

    def _create_cards_with_expiry(self, expiry_dates):
        card_ids = []
        for index, expiry_date in enumerate(expiry_dates):
            vals = self._base_vals()
            vals.update(expiry_date=expiry_date, token="tok_sort_{0}".format(index))
            card_ids.append(self.creditcard_obj.create(self.cursor, self.uid, vals))
        return card_ids

    def _search_cards_from_webclient(self, card_ids, order, **kwargs):
        with current_session.override(
            method_name="search", obj_name=self.creditcard_obj._name
        ):
            _context_stack.push({"version": ("gisce-webclient", "0.0")})
            try:
                return self.creditcard_obj.search(
                    self.cursor, self.uid, [("id", "in", card_ids)],
                    order=order, **kwargs
                )
            finally:
                _context_stack.pop()

    def test_expiry_order_ascending_uses_year_then_month(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25", "02/26", "11/25"])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "expiry_date asc"),
            [cards[3], cards[1], cards[0], cards[2]],
        )

    def test_expiry_order_descending_uses_year_then_month(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25", "02/26", "11/25"])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "expiry_date DESC"),
            [cards[2], cards[0], cards[1], cards[3]],
        )

    def test_expiry_order_without_direction_is_ascending(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25"])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "expiry_date"), cards[::-1]
        )

    def test_expiry_order_is_applied_before_pagination(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25", "02/26", "11/25"])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "expiry_date ASC", offset=1, limit=2),
            [cards[1], cards[0]],
        )

    def test_expiry_order_preserves_secondary_order(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25", "12/25"])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "expiry_date ASC, token DESC"),
            [cards[2], cards[1], cards[0]],
        )

    def test_expiry_order_keeps_equal_dates_stable_across_pages(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25", "12/25", "12/25"])
        first_page = self._search_cards_from_webclient(cards, "expiry_date ASC", limit=2)
        second_page = self._search_cards_from_webclient(
            cards, "expiry_date ASC", offset=2, limit=2
        )
        self.assertEqual(first_page + second_page, cards[1:] + cards[:1])

    def test_expiry_order_preserves_partner_join(self):
        cards = self._create_cards_with_expiry(["12/25", "01/26", "02/26"])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "partner_id ASC, expiry_date DESC"),
            cards[::-1],
        )

    def test_expiry_order_handles_missing_dates(self):
        cards = self._create_cards_with_expiry(["01/26", False, "12/25", ""])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "expiry_date ASC"),
            [cards[2], cards[0], cards[1], cards[3]],
        )
        self.assertEqual(
            self._search_cards_from_webclient(cards, "expiry_date DESC"),
            [cards[1], cards[3], cards[0], cards[2]],
        )

    def test_other_column_order_is_unchanged(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25"])
        self.assertEqual(
            self._search_cards_from_webclient(cards, "token ASC"), cards
        )

    def test_expiry_order_preserves_field_type_and_values(self):
        cards = self._create_cards_with_expiry(["01/26", "12/25"])
        self._search_cards_from_webclient(cards, "expiry_date ASC")
        self.assertEqual(self.creditcard_obj._columns["expiry_date"]._type, "char")
        values = self.creditcard_obj.read(self.cursor, self.uid, cards, ["expiry_date"])
        self.assertEqual(
            dict((value["id"], value["expiry_date"]) for value in values),
            dict(zip(cards, ["01/26", "12/25"])),
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
