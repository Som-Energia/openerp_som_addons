# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from datetime import datetime
import mock

from destral import testing
from destral.transaction import Transaction


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

    def test_get_duration_text_returns_quarter_and_year_only(self):
        result = self.backend_obj.get_duration_text(datetime(2026, 5, 17))
        self.assertEqual(result, u"2º trimestre 2026")

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

        self.assertEqual(result["label"], "1111")
        self.assertTrue(result["is_card"])

    def test_get_payment_data_returns_card_fallback_literal_without_last4(self):
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

        self.assertEqual(
            result["label"],
            u"Tarjeta de crédito (pago seleccionado mediante tarjeta bancaria)",
        )

    def test_get_payment_data_returns_bank_last4_for_non_card_mode(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_payment_data(self.cursor, self.uid, pol, context={})
        self.assertEqual(result["label"], "")

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

    def test_get_data_sets_na_discounts_without_self_consumption(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_data(self.cursor, self.uid, pol, context={})
        self.assertEqual(result["discounts"]["text"], "N/A")

    def test_get_data_reuses_existing_prices_shape_for_indexed_and_periods(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        result = self.backend_obj.get_data(self.cursor, self.uid, pol, context={})
        self.assertTrue("pricelists" in result["prices"])
        self.assertTrue("mostra_indexada" in result["prices"])
        self.assertTrue("economic_summary" in result["offer"])
        self.assertTrue(result["offer"]["economic_summary"]["power_prices"])

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

    def test_get_cnmc_data_reuses_report_v2_qr_helper(self):
        pol = self.pol_obj.browse(self.cursor, self.uid, self.contract_20td_id)
        report_v2_obj = self.openerp.pool.get("giscedata.facturacio.factura.report.v2")

        with mock.patch.object(
            report_v2_obj,
            "_get_qr_comparador_cnmc",
            return_value=("https://comparador.cnmc.gob.es/comparador/QRE?", "fake-qr"),
        ) as qr_helper:
            result = self.backend_obj.get_cnmc_data(self.cursor, self.uid, pol, context={})

        qr_helper.assert_called_with({})
        self.assertEqual(result["link_qr"], "https://comparador.cnmc.gob.es/comparador/QRE?")
        self.assertEqual(result["qr_image"], "fake-qr")
