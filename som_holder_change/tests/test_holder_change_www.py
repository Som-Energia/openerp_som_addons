# -*- coding: utf-8 -*-
from __future__ import absolute_import

from copy import deepcopy

from destral import testing
from destral.transaction import Transaction


class TestHolderChangeWww(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.www_obj = self.openerp.pool.get("som.holder.change.www")
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.polissa = self.polissa_obj.browse(
            self.cursor, self.uid, self.polissa_id
        )
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id, {"state": "activa"}
        )

    def tearDown(self):
        self.txn.stop()

    def payload(self):
        return {
            "payment": {
                "iban": "ES9121000418450200051332",
                "sepa_accepted": True,
                "voluntary_cent": True,
            },
            "supply_point": {
                "cups": self.polissa.cups.name,
                "address": self.polissa.cups.direccio,
            },
            "privacy_policy_accepted": True,
            "terms_accepted": True,
            "member": {
                "invite_token": False,
                "become_member": True,
                "link_member": False,
            },
            "especial_cases": {
                "reason_death": False,
                "reason_merge": False,
                "reason_electrodep": False,
                "attachments": {},
            },
            "holder": {
                "name": "Maria",
                "surname1": "Nova",
                "surname2": "Titular",
                "vat": "12345678Z",
                "address": "Carrer Nou, 1",
                "postal_code": "17001",
                "state": self.polissa.cups.id_municipi.state.id,
                "city": self.polissa.cups.id_municipi.id,
                "email": "maria@example.com",
                "phone1": "600000000",
                "language": "ca_ES",
            },
        }

    def test_create_request_resolves_active_contract(self):
        result = self.www_obj.create_request(
            self.cursor, self.uid, "holder-www-001", self.payload()
        )

        self.assertTrue(result["success"], result)
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["polissa_id", "owner_change_type", "state"],
        )
        self.assertEqual(request["polissa_id"][0], self.polissa_id)
        self.assertEqual(request["owner_change_type"], "T")
        self.assertEqual(request["state"], "received")

    def test_create_request_is_idempotent(self):
        first = self.www_obj.create_request(
            self.cursor, self.uid, "holder-www-002", self.payload()
        )
        second = self.www_obj.create_request(
            self.cursor, self.uid, "holder-www-002", self.payload()
        )

        self.assertEqual(second, first)

    def test_create_request_rejects_same_holder(self):
        payload = self.payload()
        payload["holder"]["vat"] = self.polissa.titular.vat.replace("ES", "")
        payload["holder"].update({
            "proxyname": "Representant Legal",
            "proxynif": "12345678Z",
        })

        result = self.www_obj.create_request(
            self.cursor, self.uid, "holder-www-003", payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "SAME_OWNER")

    def test_create_request_requires_real_consent(self):
        payload = self.payload()
        payload["payment"]["sepa_accepted"] = False

        result = self.www_obj.create_request(
            self.cursor, self.uid, "holder-www-004", payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CONSENT_REQUIRED")

    def test_create_request_derives_subrogation_from_special_case(self):
        payload = self.payload()
        payload["especial_cases"].update({
            "reason_death": True,
            "attachments": {"death": "attachment-id"},
        })

        result = self.www_obj.create_request(
            self.cursor, self.uid, "holder-www-005", payload
        )

        self.assertTrue(result["success"], result)
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["owner_change_type"],
        )
        self.assertEqual(request["owner_change_type"], "S")

    def test_create_request_rejects_inactive_contract(self):
        inactive_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        inactive = self.polissa_obj.browse(self.cursor, self.uid, inactive_id)
        payload = deepcopy(self.payload())
        payload["supply_point"]["cups"] = inactive.cups.name

        result = self.www_obj.create_request(
            self.cursor, self.uid, "holder-www-006", payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CONTRACT_NOT_ACTIVE")
