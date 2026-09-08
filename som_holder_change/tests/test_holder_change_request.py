# -*- coding: utf-8 -*-
from __future__ import absolute_import

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

    def test_create_sets_received_state(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            request_id,
            ["state"],
        )

        self.assertEqual(request["state"], "received")

    def test_write_rejects_changes_to_request_identity(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        for values in (
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
