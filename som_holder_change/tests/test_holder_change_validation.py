# -*- coding: utf-8 -*-
from __future__ import absolute_import

import unittest

from som_holder_change.www import holder_change_validation


class TestHolderChangeValidation(unittest.TestCase):

    def test_rejects_non_object_payload(self):
        error = holder_change_validation.validate_payload([])

        self.assertEqual(error["code"], "INVALID_PAYLOAD")

    def test_rejects_missing_consent_before_other_validation(self):
        payload = self.payload()
        payload["privacy_policy_accepted"] = False
        del payload["holder"]["surname1"]

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "CONSENT_REQUIRED")

    def test_rejects_conflicting_member_selection(self):
        payload = self.payload()
        payload["member"].update({"become_member": True, "link_member": True})

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "INVALID_MEMBER_SELECTION")

    def test_requires_the_attachment_for_a_special_case(self):
        payload = self.payload()
        payload["especial_cases"]["reason_death"] = True

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "MISSING_REQUIRED_FIELDS")

    def test_rejects_legacy_attachment_reference_without_an_upload(self):
        payload = self.payload()
        payload["especial_cases"].update({
            "reason_death": True,
            "attachments": {"death": "attachment-id"},
        })

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "MISSING_REQUIRED_FIELDS")

    def test_rejects_attachment_for_another_special_case(self):
        payload = self.payload()
        payload["especial_cases"]["reason_death"] = True
        payload["attachments"] = [{"category": "holder_change_merge"}]

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "INVALID_ATTACHMENT_CATEGORY")

    def test_accepts_matching_top_level_attachment_for_a_special_case(self):
        payload = self.payload()
        payload["especial_cases"]["reason_death"] = True
        payload["attachments"] = [{"category": "holder_change_death"}]

        self.assertFalse(holder_change_validation.validate_payload(payload))

    def payload(self):
        return {
            "payment_method": "bank",
            "payment": {
                "iban": "ES9121000418450200051332",
                "sepa_accepted": True,
                "voluntary_cent": True,
            },
            "supply_point": {"cups": "ES123", "address": "Carrer Nou, 1"},
            "privacy_policy_accepted": True,
            "terms_accepted": True,
            "member": {
                "invite_token": False,
                "become_member": False,
                "link_member": False,
            },
            "especial_cases": {
                "reason_death": False,
                "reason_merge": False,
                "reason_electrodep": False,
            },
            "holder": {
                "name": "Maria",
                "surname1": "Nova",
                "vat": "12345678Z",
                "address": "Carrer Nou, 1",
                "postal_code": "17001",
                "state": 1,
                "city": 1,
                "email": "maria@example.com",
                "phone1": "600000000",
                "language": "ca_ES",
            },
        }
