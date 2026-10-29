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
            "token": "tok_test_%s" % self.partner_id,
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
            self.cursor, self.uid, [("token", "=", self._base_vals()["token"])]
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
        self.assertEqual(card["token"], self._base_vals()["token"])
        self.assertEqual(card["masked_number"], "**** **** **** 1234")
        self.assertEqual(card["expiry_date"], "12/34")
        self.assertEqual(card["cof_txnid"], "cof_test_123")
        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", self._base_vals()["token"])]
            ),
            [result["id"]],
        )

    def test_resolve_for_payer_retries_a_new_token_without_duplicate_cards(self):
        created = self._resolve()

        retried = self._resolve()

        self.assertEqual(retried, {"id": created["id"], "disposition": "reused"})
        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", self._base_vals()["token"])]
            ),
            [created["id"]],
        )

    def test_resolve_for_payer_serializes_concurrent_new_token_requests(self):
        self._assert_concurrent_resolution("create", ["created", "reused"])

    def test_resolve_for_payer_serializes_concurrent_reactivation_requests(self):
        self.creditcard_obj.create(
            self.cursor, self.uid, dict(self._base_vals(), active=False)
        )
        self._assert_concurrent_resolution("write", ["reactivated", "reused"])

    def _assert_concurrent_resolution(self, mutation, expected_dispositions):
        self.cursor.commit()
        database = pooler.get_db(self.cursor.dbname)
        first_create_started = threading.Event()
        release_first_create = threading.Event()
        second_started = threading.Event()
        second_finished = threading.Event()
        results = []
        errors = []
        original_mutation = getattr(self.creditcard_obj, mutation)

        def create_while_holding_token_lock(*args, **kwargs):
            if not first_create_started.is_set():
                first_create_started.set()
                release_first_create.wait(5)
            return original_mutation(*args, **kwargs)

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
            self.creditcard_obj, mutation, side_effect=create_while_holding_token_lock
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
        self.assertEqual(
            sorted(result["disposition"] for result in results), expected_dispositions
        )
        self.assertEqual(len(set(result["id"] for result in results)), 1)
        self.assertEqual(
            self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", self._base_vals()["token"])]
            ),
            [results[0]["id"]],
        )

    def _create_card(self, **overrides):
        values = self._base_vals()
        values.update(overrides)
        return self.creditcard_obj.create(self.cursor, self.uid, values)

    def _read_card(self, card_id):
        return self.creditcard_obj.read(
            self.cursor, self.uid, card_id,
            ["active", "partner_id", "token", "masked_number", "expiry_date", "cof_txnid"],
            context={"active_test": False},
        )

    def test_resolve_for_payer_creates_card_for_each_different_metadata_field(self):
        original_id = self._create_card()
        original = self._read_card(original_id)
        for field_name, value in (
            ("masked_number", "**** **** **** 9999"),
            ("expiry_date", "11/35"),
            ("cof_txnid", "cof_other"),
        ):
            card_data = self._base_vals()
            card_data[field_name] = value

            result = self._resolve(card_data)

            self.assertEqual(result["disposition"], "created")
            self.assertNotEqual(result["id"], original_id)
            self.assertEqual(self._read_card(result["id"])[field_name], value)
            self.assertEqual(
                self._resolve(card_data),
                {"id": result["id"], "disposition": "reused"},
            )
        self.assertEqual(self._read_card(original_id), original)

    def test_resolve_for_payer_reuses_exact_match_among_different_metadata(self):
        self._create_card(cof_txnid="cof_other")
        exact_id = self._create_card()

        self.assertEqual(self._resolve(), {"id": exact_id, "disposition": "reused"})

    def test_resolve_for_payer_reactivates_exact_inactive_card(self):
        card_id = self._create_card(active=False)
        before = self._read_card(card_id)

        result = self._resolve()

        self.assertEqual(result, {"id": card_id, "disposition": "reactivated"})
        self.assertEqual(self._read_card(card_id), dict(before, active=True))
        self.assertEqual(self._resolve(), {"id": card_id, "disposition": "reused"})

    def test_resolve_for_payer_prefers_active_over_duplicate_inactive_cards(self):
        inactive_ids = [self._create_card(active=False) for unused in range(2)]
        active_id = self._create_card()

        result = self._resolve()

        self.assertEqual(result, {"id": active_id, "disposition": "reused"})
        for card_id in inactive_ids:
            self.assertFalse(self._read_card(card_id)["active"])

    def test_resolve_for_payer_reactivates_exact_card_despite_other_active_metadata(self):
        other_id = self._create_card(cof_txnid="cof_other")
        inactive_id = self._create_card(active=False)
        other_before = self._read_card(other_id)

        result = self._resolve()

        self.assertEqual(result, {"id": inactive_id, "disposition": "reactivated"})
        self.assertTrue(self._read_card(inactive_id)["active"])
        self.assertEqual(self._read_card(other_id), other_before)

    def test_resolve_for_payer_does_not_reactivate_different_inactive_metadata(self):
        inactive_id = self._create_card(active=False, cof_txnid="cof_other")
        before = self._read_card(inactive_id)

        result = self._resolve()

        self.assertEqual(result["disposition"], "created")
        self.assertNotEqual(result["id"], inactive_id)
        self.assertEqual(self._read_card(inactive_id), before)

    def test_resolve_for_payer_does_not_reactivate_another_payers_card(self):
        inactive_id = self._create_card(active=False)
        other_partner_id = self.partner_obj.create(
            self.cursor, self.uid, {"name": "Other payer"}
        )

        result = self._resolve(partner_id=other_partner_id)

        self.assertEqual(result["disposition"], "created")
        self.assertEqual(self._read_card(result["id"])["partner_id"][0], other_partner_id)
        self.assertFalse(self._read_card(inactive_id)["active"])

    def test_resolve_for_payer_rejects_duplicate_active_exact_matches(self):
        card_ids = [self._create_card() for unused in range(2)]
        before = [self._read_card(card_id) for card_id in card_ids]

        with self.assertRaises(osv.except_osv):
            self._resolve()

        self.assertEqual([self._read_card(card_id) for card_id in card_ids], before)

    def test_resolve_for_payer_rejects_duplicate_inactive_exact_matches(self):
        card_ids = [self._create_card(active=False) for unused in range(2)]
        before = [self._read_card(card_id) for card_id in card_ids]

        with self.assertRaises(osv.except_osv):
            self._resolve()

        self.assertEqual([self._read_card(card_id) for card_id in card_ids], before)

    def test_resolve_for_payer_requires_write_permission_to_reactivate(self):
        card_id = self._create_card(active=False)
        original_check_perm = self.creditcard_obj.check_perm

        def check_perm(cursor, uid, operation, **kwargs):
            if operation == "write":
                raise osv.except_osv("Access denied", "Cannot reactivate cards")
            return original_check_perm(cursor, uid, operation, **kwargs)

        with mock.patch.object(self.creditcard_obj, "check_perm", side_effect=check_perm):
            with self.assertRaises(osv.except_osv):
                self._resolve()

        self.assertFalse(self._read_card(card_id)["active"])

    def test_resolve_for_payer_prefers_active_even_with_active_test_disabled(self):
        self._create_card(active=False)
        active_id = self._create_card()
        context = {"active_test": False}

        result = self.creditcard_obj.resolve_for_payer(
            self.cursor, self.uid, self.partner_id, self._base_vals(), context=context
        )

        self.assertEqual(result, {"id": active_id, "disposition": "reused"})
        self.assertEqual(context, {"active_test": False})

    def test_resolve_for_payer_creates_card_when_token_belongs_to_another_payer(self):
        existing_card_id = self.creditcard_obj.create(
            self.cursor, self.uid, self._base_vals()
        )
        other_partner_id = self.partner_obj.create(
            self.cursor, self.uid, {"name": "Other card payer"}
        )

        result = self._resolve(partner_id=other_partner_id)

        self.assertEqual(result["disposition"], "created")
        self.assertEqual(
            self.creditcard_obj.read(
                self.cursor, self.uid, result["id"], ["partner_id"]
            )["partner_id"][0],
            other_partner_id,
        )
        self.assertEqual(
            sorted(self.creditcard_obj.search(
                self.cursor, self.uid, [("token", "=", self._base_vals()["token"])]
            )),
            sorted([existing_card_id, result["id"]]),
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
