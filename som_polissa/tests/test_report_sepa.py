# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import unittest

import mock
from destral import testing
from destral.transaction import Transaction
from mako.lookup import TemplateLookup
from mako.template import Template


ADDONS_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SEPA_TEMPLATE = os.path.join(ADDONS_PATH, "som_polissa", "report", "sepa.mako")


class TestReportBackendMandatSepa(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.backend = self.openerp.pool.get("report.backend.mandat.sepa")
        self.mandate = self.openerp.pool.get("payment.mandate")

    def tearDown(self):
        self.txn.stop()

    def test_get_lang_delegates_to_authoritative_mandate_backend(self):
        mandate_backend = self.openerp.pool.get("report.backend.mandat")
        context = {"test": True}

        with mock.patch.object(
            mandate_backend, "get_lang", return_value="ca_ES"
        ) as get_lang:
            result = self.backend.get_lang(
                self.cursor, self.uid, 42, context=context
            )

        self.assertEqual(result, "ca_ES")
        get_lang.assert_called_once_with(
            self.cursor, self.uid, 42, context=context
        )

    def test_sepa_lang_uses_catalan_only_for_exact_ca_es(self):
        with mock.patch.object(
            self.backend, "get_lang", return_value="ca_ES"
        ):
            result = self.backend._get_sepa_lang(
                self.cursor, self.uid, 42, context={}
            )

        self.assertEqual(result, "ca_ES")

    def test_sepa_lang_falls_back_to_spanish(self):
        with mock.patch.object(
            self.backend, "get_lang", return_value="en_US"
        ):
            result = self.backend._get_sepa_lang(
                self.cursor, self.uid, 42, context={}
            )

        self.assertEqual(result, "es_ES")

    def test_sign_date_uses_catalan_month_and_calendar_year(self):
        result = self.mandate._format_sign_date("2018-12-31", "ca_ES")

        self.assertEqual(result, u"31 desembre de 2018")

    def test_sign_date_uses_spanish_month(self):
        result = self.mandate._format_sign_date("2024-01-15", "es_ES")

        self.assertEqual(result, u"15 enero de 2024")


class TestSepaTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lookup = TemplateLookup(directories=[ADDONS_PATH], input_encoding="utf-8")
        with open(SEPA_TEMPLATE, "r") as template_file:
            template_source = template_file.read()
        cls.template = Template(
            template_source, lookup=lookup, input_encoding="utf-8"
        )

    def mandate_data(self, lang, is_business, reference):
        return {
            "company_logo": "",
            "creditor_address": "Carrer Major, 1",
            "creditor_city": "Girona",
            "creditor_code": "ES00ZZZ000000000",
            "creditor_country": "Espanya",
            "creditor_name": "Som Energia",
            "creditor_province": "Girona",
            "debtor_address": "Carrer Nou, 2",
            "debtor_country": "Espanya",
            "debtor_iban_print": "ES00 0000 0000 0000 0000 0000",
            "debtor_name": "Test",
            "debtor_province": "Barcelona",
            "is_business": is_business,
            "lang": lang,
            "order_reference": reference,
            "recurring": "checked",
            "sign_date": "15 gener de 2024",
            "single_payment": "",
            "swift": "TESTBIC0",
        }

    def render(self, objects):
        return self.template.render_unicode(
            objects=objects,
            addons_path=ADDONS_PATH,
        )

    def test_mixed_language_core_and_b2b_mandates_render_independently(self):
        objects = [
            self.mandate_data("ca_ES", False, "CA-CORE"),
            self.mandate_data("ca_ES", True, "CA-B2B"),
            self.mandate_data("es_ES", False, "ES-CORE"),
            self.mandate_data("es_ES", True, "ES-B2B"),
        ]

        result = self.render(objects)

        self.assertIn(u"Ordre de domiciliació de dèbit directe SEPA", result)
        self.assertIn(u"operacions entre empreses i/o autònoms", result)
        self.assertIn(u"Orden de domiciliación de adeudo directo SEPA", result)
        self.assertIn(u"operaciones exclusivamente entre empresas", result)
        self.assertIn(u"SEPA Direct Debit Mandate", result)
        self.assertEqual(result.count(u"mandate-page"), 3)
