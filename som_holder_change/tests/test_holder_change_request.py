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
            {"payload": {"contract_owner": {"vat": "B12345678"}}},
            {"polissa_id": self.polissa_id},
            {"cups": "ES00000000000000000000"},
            {"owner_change_type": "S"},
            {"report_snapshot": {"version": 1}},
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

    def request_values(self, **values):
        result = {
            "polissa_id": self.polissa_id,
            "cups": "ES12345678901234567890",
            "owner_change_type": "T",
            "payload": {
                "contract_owner": {"vat": "12345678Z", "name": "New holder"},
                "iban": "ES9121000418450200051332",
            },
        }
        result.update(values)
        return result


class TestHolderChangeAddress(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestHolderChangeAddress, self).setUp()
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        polissa_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.polissa = self.openerp.pool.get("giscedata.polissa").browse(
            self.cursor, self.uid, polissa_id
        )

    def test_new_card_holder_address_uses_state_country_without_iban(self):
        self._check_new_holder_address_country({"payment_type": "tpv"})

    def test_new_holder_address_country_does_not_follow_foreign_iban(self):
        self._check_new_holder_address_country({
            "payment_type": "remesa", "iban": "DE89370400440532013000",
        })

    def _check_new_holder_address_country(self, payment_values):
        payload = {
            "contract_owner": {
                "name": "Maria",
                "surname": "Nova Titular",
                "vat": "12345678Z",
                "address": {
                    "street": "Carrer Nou",
                    "number": "1",
                    "postal_code": "17001",
                    "state_id": self.polissa.cups.id_municipi.state.id,
                    "city_id": self.polissa.cups.id_municipi.id,
                },
                "email": "maria@example.com",
                "phone": "600000000",
            },
        }
        payload.update(payment_values)
        partner_id = self.openerp.pool.get("res.partner").create(
            self.cursor, self.uid, {"name": "New address holder", "vat": "ES76543210S"}
        )
        request_id = self.request_obj.create(
            self.cursor, self.uid,
            {"polissa_id": self.polissa.id, "cups": self.polissa.cups.name,
             "owner_change_type": "T", "payload": payload},
        )
        request = self.request_obj.browse(self.cursor, self.uid, request_id)
        address_id = self.request_obj._create_holder_address(
            self.cursor, self.uid, request, partner_id
        )
        address = self.openerp.pool.get("res.partner.address").browse(
            self.cursor, self.uid, address_id
        )
        self.assertEqual(address.country_id.code, "ES")
        self.assertEqual(address.country_id.id, address.state_id.country_id.id)
