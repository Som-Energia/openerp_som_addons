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
        payload["privacy_conditions"] = False
        del payload["contract_owner"]["surname"]

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "CONSENT_REQUIRED")

    def test_rejects_invalid_member_selection(self):
        payload = self.payload()
        payload["linked_member"] = "invalid"

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

    def test_rejects_special_attachment_without_special_case(self):
        payload = self.payload()
        payload["attachments"] = [{"category": "holder_change_death"}]

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "INVALID_ATTACHMENT_CATEGORY")

    def test_rejects_more_than_one_special_case(self):
        payload = self.payload()
        payload["especial_cases"].update({
            "reason_death": True,
            "reason_electrodep": True,
        })

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "INVALID_SPECIAL_CASE")

    def test_accepts_disabled_donation(self):
        payload = self.payload()
        payload["donation"] = False

        self.assertFalse(holder_change_validation.validate_payload(payload))

    def test_rejects_non_boolean_donation(self):
        payload = self.payload()
        payload["donation"] = "false"

        error = holder_change_validation.validate_payload(payload)

        self.assertEqual(error["code"], "INCORRECT_PARAM_TYPE")

    def payload(self):
        return {
            "payment_type": "remesa",
            "iban": "ES9121000418450200051332",
            "sepa_accepted": True,
            "donation": True,
            "contract_info": {"cups": "ES123"},
            "privacy_conditions": True,
            "general_contract_terms_accepted": True,
            "linked_member": "without_member",
            "especial_cases": {
                "reason_death": False,
                "reason_merge": False,
                "reason_electrodep": False,
            },
            "contract_owner": {
                "name": "Maria",
                "surname": "Nova",
                "vat": "12345678Z",
                "address": {
                    "street": "Carrer Nou",
                    "number": "1",
                    "postal_code": "17001",
                    "state_id": 1,
                    "city_id": 1,
                },
                "email": "maria@example.com",
                "phone": "600000000",
                "lang": "ca_ES",
            },
        }
