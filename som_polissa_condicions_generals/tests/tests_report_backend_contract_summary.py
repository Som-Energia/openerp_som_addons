# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from datetime import datetime
import os
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


class TestSummaryOfferTemplate(unittest.TestCase):
    def test_renders_current_and_future_price_blocks_in_order(self):
        economic_summary = {
            "tax_text": "",
            "generation_prices": [],
            "cooperative_fee": False,
            "autoconsum_price": False,
        }
        current_summary = economic_summary.copy()
        current_summary.update({
            "power_prices": [{"period": "P1", "value": 10.0}],
            "energy_prices": [{"period": "P1", "value": 0.1}],
        })
        future_summary = economic_summary.copy()
        future_summary.update({
            "power_prices": [{"period": "P1", "value": 20.0}],
            "energy_prices": [{"period": "P1", "value": 0.2}],
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
            "has_generation": False,
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

        self.assertEqual(result.count(u"Resum econòmic"), 1)
        positions = [
            result.index(u"Resum econòmic"),
            result.index("Current validity"),
            result.index("10.000000"),
            result.index("0.100000"),
            result.index("Future validity"),
            result.index("20.000000"),
            result.index("0.200000"),
        ]
        self.assertEqual(positions, sorted(positions))


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
