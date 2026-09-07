# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
import hashlib

from osv import osv

from destral import testing
from destral.transaction import Transaction


class TestHolderChangeRequest(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

    def tearDown(self):
        self.txn.stop()

    def request_values(self, **values):
        result = {
            "request_key": "holder-change-001",
            "polissa_id": self.polissa_id,
            "cups": "ES12345678901234567890",
            "owner_change_type": "T",
            "payload": {
                "holder": {"vat": "12345678Z", "name": "New holder"},
                "payment": {"iban": "ES9121000418450200051332"},
            },
        }
        result.update(values)
        return result

    def test_create_sets_received_state_and_payload_hash(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            request_id,
            ["state", "payload_hash"],
        )

        self.assertEqual(request["state"], "received")
        self.assertEqual(
            request["payload_hash"],
            "af9bff92d1cf48de4f72ae16248f2a69a2a2a167dcfeb729681e701126672a99",
        )

    def test_create_or_get_is_idempotent_for_same_payload(self):
        first_id = self.request_obj.create_or_get(
            self.cursor, self.uid, self.request_values()
        )
        second_id = self.request_obj.create_or_get(
            self.cursor, self.uid, self.request_values()
        )

        self.assertEqual(second_id, first_id)

    def test_create_or_get_rejects_same_key_with_different_payload(self):
        self.request_obj.create_or_get(
            self.cursor, self.uid, self.request_values()
        )
        changed_values = self.request_values(payload={"holder": {"vat": "B12345678"}})

        with self.assertRaises(osv.except_osv):
            self.request_obj.create_or_get(
                self.cursor, self.uid, changed_values
            )

    def test_write_rejects_changes_to_request_identity(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        for values in (
            {"request_key": "another-key"},
            {"payload": {"holder": {"vat": "B12345678"}}},
            {"polissa_id": self.polissa_id},
            {"cups": "ES00000000000000000000"},
            {"owner_change_type": "S"},
        ):
            with self.assertRaises(osv.except_osv):
                self.request_obj.write(
                    self.cursor, self.uid, [request_id], values
                )

    def test_write_allows_workflow_fields(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        self.request_obj.write(
            self.cursor,
            self.uid,
            [request_id],
            {"state": "validation_error", "error_message": "Invalid IBAN"},
        )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            request_id,
            ["state", "error_message"],
        )
        self.assertEqual(request["state"], "validation_error")
        self.assertEqual(request["error_message"], "Invalid IBAN")

    def test_freeze_m101_is_idempotent_and_rejects_different_pdf(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )
        pdf = b"%PDF-frozen"

        self.request_obj.freeze_m101(
            self.cursor, self.uid, request_id, pdf
        )
        self.request_obj.freeze_m101(
            self.cursor, self.uid, request_id, pdf
        )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            request_id,
            ["m101_pdf", "m101_pdf_hash"],
        )
        self.assertEqual(base64.b64decode(request["m101_pdf"]), pdf)
        self.assertEqual(
            request["m101_pdf_hash"], hashlib.sha256(pdf).hexdigest()
        )
        with self.assertRaises(osv.except_osv):
            self.request_obj.freeze_m101(
                self.cursor, self.uid, request_id, b"%PDF-different"
            )
