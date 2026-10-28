# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from datetime import datetime
import os
import re
import unittest

from destral import testing
from destral.transaction import Transaction
from mako.template import Template


SUMMARY_OFFER_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "report",
    "components",
    "summary_offer.mako",
)
CONTRACT_SUMMARY_CSS = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "report",
    "contract_summary_puppeteer.css",
)


class TestSummaryOfferTemplate(unittest.TestCase):
    def test_renders_current_and_future_price_blocks_in_order(self):
        economic_summary = {
            "tax_text": "",
            "cooperative_fee": False,
            "autoconsum_price": False,
        }
        current_summary = economic_summary.copy()
        current_summary.update({
            "power_prices": [{"period": "P1", "value": 10.0}],
            "energy_prices": [{"period": "P1", "value": 0.1}],
            "generation_prices": [{"period": "P1", "value": 0.03}],
        })
        future_summary = economic_summary.copy()
        future_summary.update({
            "power_prices": [{"period": "P1", "value": 20.0}],
            "energy_prices": [{"period": "P1", "value": 0.2}],
            "generation_prices": [{"period": "P1", "value": 0.04}],
        })
        offer = {
            "tariff_label": "2.0TD",
            "duration_quarter": 1,
            "duration_year": 2026,
            "powers": [],
            "is_indexed": False,
            "price_summaries": [
                {
                    "validity_text": "Current validity",
                    "economic_summary": current_summary,
                },
                {
                    "validity_text": "Future validity",
                    "economic_summary": future_summary,
                },
            ],
        }
        features = {
            "has_generation": True,
            "has_autoconsum": False,
            "has_gurb": False,
        }

        result = Template(filename=SUMMARY_OFFER_TEMPLATE).get_def(
            "summary_offer"
        ).render_unicode(
            offer=offer,
            features=features,
            gurb=False,
            _=lambda text: text,
            formatLang=lambda value, digits: u"{0:.6f}".format(value),
        )

        self.assertEqual(
            result.count('<div class="summary-box summary-box--offer">'), 1
        )
        self.assertEqual(result.count('<div class="price-summary">'), 2)
        self.assertEqual(result.count('<table class="summary-table">'), 2)

        price_blocks = result.split('<div class="price-summary">')[1:]
        self.assertEqual(price_blocks[0].count(u"Resum econòmic"), 1)
        self.assertNotIn(u"Resum econòmic", price_blocks[1])
        self.assertLess(
            result.index(u"Potències contractades"),
            result.index(u"Resum econòmic"),
        )
        self.assertLess(
            price_blocks[0].index(u"Resum econòmic"),
            price_blocks[0].index("Current validity"),
        )
        expected_blocks = [
            (
                price_blocks[0], "Current validity", "10.000000",
                "0.100000", "0.030000",
            ),
            (
                price_blocks[1], "Future validity", "20.000000",
                "0.200000", "0.040000",
            ),
        ]
        for block, validity, power, energy, generation in expected_blocks:
            self.assertEqual(block.count('<table class="summary-table">'), 1)
            self.assertEqual(block.count("Generation (€/kWh)"), 1)
            positions = [
                block.index(validity),
                block.index(power),
                block.index(energy),
                block.index("Generation (€/kWh)"),
                block.index(generation),
            ]
            self.assertEqual(positions, sorted(positions))

    def test_offer_box_can_paginate_while_each_price_summary_stays_together(self):
        with open(CONTRACT_SUMMARY_CSS, "r") as css_file:
            css = css_file.read()

        self.assertTrue(re.search(
            r"\.summary-box\s*\{[^}]*break-inside:\s*avoid;", css
        ))
        self.assertTrue(re.search(
            r"\.summary-box--offer\s*\{[^}]*break-inside:\s*auto;", css
        ))
        self.assertTrue(re.search(
            r"\.price-summary\s*\{[^}]*break-inside:\s*avoid;", css
        ))


class TestReportBackendContractSummary(testing.OOTestCase):
    def get_ref(self, module, ref):
        ir_model = self.openerp.pool.get("ir.model.data")
        return ir_model._get_obj(self.cursor, self.uid, module, ref).id

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.backend_obj = self.openerp.pool.get("report.backend.contract.summary")
        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.card_obj = self.openerp.pool.get("res.partner.creditcard")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.contract_20td_id = self.get_ref("giscedata_polissa", "polissa_tarifa_018")

    def tearDown(self):
        self.txn.stop()

    def test_get_duration_data_returns_quarter_and_year(self):
        result = self.backend_obj.get_duration_data(datetime(2026, 5, 17))
        self.assertEqual(result, (2, 2026))

    def test_get_payment_data_returns_card_last4_when_available(self):
        card_payment_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        card_id = self.card_obj.create(self.cursor, self.uid, {
            "partner_id": pol.pagador.id,
            "token": "tok_contract_summary_1111",
            "expiry_date": "12/35",
            "masked_number": "**** **** **** 1111",
        })
        self.pol_obj.write(self.cursor, self.uid, [pol.id], {
            "tipo_pago": card_payment_type_id,
            "creditcard": card_id,
        })

        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_payment_data(self.cursor, self.uid, pol, context={})

        self.assertEqual(result["label"], "**** **** **** 1111")
        self.assertTrue(result["is_card"])

    def test_get_payment_data_returns_empty_label_for_card_without_last4(self):
        card_payment_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        card_id = self.card_obj.create(self.cursor, self.uid, {
            "partner_id": pol.pagador.id,
            "token": "tok_contract_summary_empty",
            "expiry_date": "12/35",
            "masked_number": "",
        })
        self.pol_obj.write(self.cursor, self.uid, [pol.id], {
            "tipo_pago": card_payment_type_id,
            "creditcard": card_id,
        })

        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_payment_data(self.cursor, self.uid, pol, context={})

        self.assertEqual(result["label"], "")
        self.assertEqual(result["last4"], "")
        self.assertTrue(result["is_card"])

    def test_get_payment_data_returns_bank_last4_for_non_card_mode(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_payment_data(self.cursor, self.uid, pol, context={})
        self.assertTrue(result["label"] in ("", "**** **** **** **** 6789"))

    def test_get_section_flags_hides_optional_paragraphs_without_generation_or_gurb(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_section_flags(self.cursor, self.uid, pol, context={})
        self.assertFalse(result["show_section_6_final_paragraph"])
        self.assertFalse(result["show_section_7_final_paragraph"])

    def test_get_section_flags_hides_section_6_gurb_text_for_generation_only(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        self.pol_obj.write(self.cursor, self.uid, [pol.id], {"te_assignacio_gkwh": True})

        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_section_flags(self.cursor, self.uid, pol, context={})

        self.assertFalse(result["show_section_6_final_paragraph"])
        self.assertTrue(result["show_section_7_final_paragraph"])

    def test_get_data_omits_optional_supply_fields_when_empty(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        self.pol_obj.write(self.cursor, self.uid, [pol.id], {"name": False})

        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_data(self.cursor, self.uid, pol, context={})

        self.assertFalse("contract_number" in result["supply"])

    def test_get_data_exposes_discount_visibility_without_self_consumption(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_data(self.cursor, self.uid, pol, context={})
        self.assertFalse(result["discounts"]["show_legal_text"])

    def test_get_data_reuses_existing_prices_shape_for_indexed_and_periods(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_data(self.cursor, self.uid, pol, context={})
        self.assertTrue("pricelists" in result["prices"])
        self.assertTrue("mostra_indexada" in result["prices"])
        self.assertTrue("price_summaries" in result["offer"])
        self.assertTrue(
            result["offer"]["price_summaries"][0]["economic_summary"]["power_prices"]
        )

    def test_get_offer_data_builds_current_and_future_price_summaries_in_order(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        prices = {
            "mostra_indexada": False,
            "pricelists": [
                {
                    "text_vigencia": "Current prices",
                    "power_prices_untaxed": {"P1": 1.0},
                    "energy_prices_untaxed": {"P1": 0.1},
                },
                {
                    "text_vigencia": "Future prices",
                    "power_prices_untaxed": {"P1": 2.0},
                    "energy_prices_untaxed": {"P1": 0.2},
                },
            ],
        }

        result = self.backend_obj.get_offer_data(
            self.cursor, self.uid, pol, prices, context={}
        )

        self.assertFalse(result["is_indexed"])
        self.assertEqual(
            [summary["validity_text"] for summary in result["price_summaries"]],
            ["Current prices", "Future prices"],
        )
        self.assertEqual(
            [
                summary["economic_summary"]["energy_prices"][0]["value"]
                for summary in result["price_summaries"]
            ],
            [0.1, 0.2],
        )
        self.assertTrue(
            all(
                "validity_text" not in summary["economic_summary"]
                for summary in result["price_summaries"]
            )
        )
        self.assertTrue(
            all(
                "is_indexed" not in summary["economic_summary"]
                for summary in result["price_summaries"]
            )
        )

    def test_get_prices_data_ignores_tarifa_provisional_context(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)

        result = self.backend_obj.get_prices_data(self.cursor, self.uid, pol, context={
            "tarifa_provisional": {
                "preus_provisional_energia": {"P1": 99.0},
                "preus_provisional_potencia": {"P1": 88.0},
            }
        })

        self.assertFalse(result["dict_preus_tp_energia"])
        self.assertFalse(result["dict_preus_tp_potencia"])

    def test_get_polissa_data_ignores_tarifa_provisional_context(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)

        result = self.backend_obj.get_polissa_data(self.cursor, self.uid, pol, context={
            "tarifa_provisional": {
                "preus_provisional_energia": {"P1": 99.0},
            }
        })

        self.assertNotEqual(result["tarifa_mostrar"], "Tarifa Períodes Empresa")
