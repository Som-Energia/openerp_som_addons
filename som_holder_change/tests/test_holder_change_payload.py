# -*- coding: utf-8 -*-
from __future__ import absolute_import

import unittest

from som_holder_change.models import holder_change_payload


class TestHolderChangePayload(unittest.TestCase):

    def test_normalize_holder_vat_adds_spanish_prefix(self):
        self.assertEqual(
            holder_change_payload.normalize_holder_vat({"vat": "12345678z"}),
            "ES12345678Z",
        )

    def test_normalize_holder_vat_preserves_existing_prefix(self):
        self.assertEqual(
            holder_change_payload.normalize_holder_vat({"vat": "esB12345678"}),
            "ESB12345678",
        )

    def test_clean_iban_keeps_only_uppercase_alphanumeric_characters(self):
        self.assertEqual(
            holder_change_payload.clean_iban("es91 2100-0418.4502/0005 1332"),
            "ES9121000418450200051332",
        )

    def test_holder_full_name_uses_surnames_for_individuals(self):
        self.assertEqual(
            holder_change_payload.holder_full_name({
                "vat": "12345678Z",
                "name": "Maria",
                "surname1": "Nova",
                "surname2": "Titular",
            }),
            "Nova Titular, Maria",
        )

    def test_holder_full_name_uses_company_name_for_legal_entities(self):
        self.assertEqual(
            holder_change_payload.holder_full_name({
                "vat": "B12345678",
                "name": "Cooperativa Exemple",
            }),
            "Cooperativa Exemple",
        )

    def test_append_observation_skips_equivalent_whitespace(self):
        self.assertEqual(
            holder_change_payload.append_observation(
                "Existing\nobservation",
                "Existing observation",
            ),
            "Existing\nobservation",
        )

    def test_append_observation_prepends_new_content(self):
        self.assertEqual(
            holder_change_payload.append_observation("Old observation", "New observation"),
            "New observation\nOld observation",
        )

    def test_special_case_document_spec_uses_legacy_priority(self):
        self.assertEqual(
            holder_change_payload.special_case_document_spec({
                "reason_death": True,
                "reason_merge": True,
                "reason_electrodep": True,
            }),
            ("holder_change_death", "Certificat defunció"),
        )

    def test_special_case_document_spec_returns_false_without_special_case(self):
        self.assertEqual(
            holder_change_payload.special_case_document_spec({}),
            (False, False),
        )
