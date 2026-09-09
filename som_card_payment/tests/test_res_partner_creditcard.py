# -*- coding: utf-8 -*-
from __future__ import absolute_import

import threading

from destral import testing
import mock
from osv import osv
from osv.orm import FieldsValidationException
import pooler


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
        self.assertEqual(card["masked_number"], "**** **** **** 1234")
        self.assertEqual(card["expiry_date"], "12/34")
        self.assertEqual(card["cof_txnid"], "cof_test_123")
        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", "tok_test_123")]
            ),
            [result["id"]],
        )

    def test_resolve_for_payer_retries_a_new_token_without_duplicate_cards(self):
        created = self._resolve()

        retried = self._resolve()

        self.assertEqual(retried, {"id": created["id"], "disposition": "reused"})
        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", "tok_test_123")]
            ),
            [created["id"]],
        )

    def test_resolve_for_payer_serializes_concurrent_new_token_requests(self):
        self.cursor.commit()
        database = pooler.get_db(self.cursor.dbname)
        first_create_started = threading.Event()
        release_first_create = threading.Event()
        second_started = threading.Event()
        second_finished = threading.Event()
        results = []
        errors = []
        original_create = self.creditcard_obj.create

        def create_while_holding_token_lock(*args, **kwargs):
            if not first_create_started.is_set():
                first_create_started.set()
                release_first_create.wait(5)
            return original_create(*args, **kwargs)

        def resolve_in_transaction(started, finished):
            cursor = database.cursor()
            try:
                started.set()
                result = self.creditcard_obj.resolve_for_payer(
                    cursor, self.uid, self.partner_id, self._base_vals()
                )
                cursor.commit()
                results.append(result)
            except Exception as error:
                cursor.rollback()
                errors.append(error)
            finally:
                finished.set()
                cursor.close()

        with mock.patch.object(
            self.creditcard_obj, "create", side_effect=create_while_holding_token_lock
        ):
            first = threading.Thread(
                target=resolve_in_transaction,
                args=(threading.Event(), threading.Event()),
            )
            first.start()
            self.assertTrue(first_create_started.wait(5))
            second = threading.Thread(
                target=resolve_in_transaction,
                args=(second_started, second_finished),
            )
            second.start()
            self.assertTrue(second_started.wait(5))
            self.assertFalse(second_finished.wait(0.5))
            release_first_create.set()
            first.join(5)
            second.join(5)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(sorted(result["disposition"] for result in results), ["created", "reused"])
        self.assertEqual(len(set(result["id"] for result in results)), 1)
        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", "tok_test_123")]
            ),
            [results[0]["id"]],
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
