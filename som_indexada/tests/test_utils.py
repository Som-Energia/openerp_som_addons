# -*- coding: utf-8 -*-
from __future__ import absolute_import, division

import unittest
from datetime import datetime

import mock
from som_indexada import utils
from som_indexada import taxes


class TestCalculateNewIndexedPrices(unittest.TestCase):

    def _calculate_prices(self, old_factor, new_factor, factor_change=None,
                          social_prices=None, tax_rates=None):
        pol = mock.Mock()
        pol.tarifa.name = '2.0TD'
        pol.cups.conany_kwh = 1000
        pol.potencia = 2
        power = mock.Mock(potencia=2)
        power.periode_id.name = 'P1'
        pol.potencies_periode = [power]
        pol.pool.get.return_value.get.return_value = (
            "{'2.0TD': {'preu_sense_F': 100}}"
        )
        prices = [
            {'factor_k': old_factor, 'tp': {'P1': 10}},
            {'factor_k': new_factor, 'tp': {'P1': 20}},
        ]
        tax_rates = tax_rates or [{'IVA': 0.21, 'IE': 0.0511}] * 2
        tax_results = []
        for factor, power_price, rates in zip(
                [old_factor, new_factor], [20, 40], tax_rates):
            key = 'k_old' if not tax_results else 'k_new'
            factor = (factor_change or {}).get(key, factor)
            base = 100 + 1015 * factor + power_price
            tax_results.append((
                base * (1 + rates.get('IE', 0))
                * (1 + rates.get('IGIC', rates.get('IVA', 0))), rates
            ))
        with mock.patch.object(utils, 'get_preus', side_effect=prices), \
                mock.patch.object(utils, 'get_fs_from_k_change',
                                  return_value=factor_change or {}), \
                mock.patch.object(utils, 'get_tax_polissa', return_value=pol), \
                mock.patch.object(utils, 'get_bo_social_estimation',
                                  side_effect=social_prices or [(0, 0)] * 2), \
                mock.patch.object(utils, 'compute_estimation_taxes',
                                  side_effect=tax_results):
            return utils.calculate_new_indexed_prices(None, 1, pol, context={})

    def _assert_estimation(self, result, old_energy, new_energy):
        old_total = old_energy + 20
        new_total = new_energy + 40
        self.assertAlmostEqual(result['import_energia_anual_antiga'], old_energy)
        self.assertAlmostEqual(result['import_energia_anual_nova'], new_energy)
        self.assertAlmostEqual(result['import_total_anual_antiga'], old_total)
        self.assertAlmostEqual(result['import_total_anual_nova'], new_total)
        self.assertAlmostEqual(
            result['impacte_perc'], (new_total - old_total) / old_total * 100
        )
        self.assertAlmostEqual(
            result['import_total_anual_nova_amb_impost'], new_total * 1.0511 * 1.21
        )
        self.assertAlmostEqual(
            result['impacte_perc_amb_impost'], result['impacte_perc']
        )

    def test_pricelist_factors_are_already_in_kwh(self):
        result = self._calculate_prices(0.005, 0.007)

        self.assertAlmostEqual(result['f_antiga_kwh'], 0.005)
        self.assertAlmostEqual(result['f_nova_kwh'], 0.007)
        self._assert_estimation(result, 105.075, 107.105)

    def test_factor_changes_override_pricelist_in_kwh(self):
        result = self._calculate_prices(
            0.005, 0.007, {'k_old': 0.011, 'k_new': 0.013}
        )

        self.assertAlmostEqual(result['f_antiga_kwh'], 0.011)
        self.assertAlmostEqual(result['f_nova_kwh'], 0.013)
        self._assert_estimation(result, 111.165, 113.195)

    def test_decimal_factors_keep_precision(self):
        result = self._calculate_prices(0.0055, 0.00725)

        self.assertAlmostEqual(result['f_antiga_kwh'], 0.0055)
        self.assertAlmostEqual(result['f_nova_kwh'], 0.00725)
        self._assert_estimation(result, 105.5825, 107.35875)

    def test_integer_factors_are_not_divided_or_truncated(self):
        result = self._calculate_prices(0, 1)
        self.assertEqual(result['f_nova_kwh'], 1)
        self._assert_estimation(result, 100, 1115)

    def test_social_charge_included_once_with_its_own_taxes(self):
        result = self._calculate_prices(
            0.005, 0.007, social_prices=[(10, 12.1), (20, 24.2)]
        )
        self.assertAlmostEqual(result['import_total_anual_antiga'], 135.075)
        self.assertAlmostEqual(result['import_total_anual_nova'], 167.105)
        self.assertAlmostEqual(
            result['import_total_anual_nova_amb_impost'],
            147.105 * 1.0511 * 1.21 + 24.2
        )
        self.assertEqual(result['import_bo_social_anual_nova'], 20)

    def test_tax_rates_can_change_between_scenarios(self):
        result = self._calculate_prices(
            0.005, 0.007,
            tax_rates=[{'IVA': 0.05, 'IE': 0.005}, {'IGIC': 0.03}]
        )
        self.assertAlmostEqual(
            result['import_total_anual_antiga_amb_impost'], 125.075 * 1.005 * 1.05
        )
        self.assertAlmostEqual(
            result['import_total_anual_nova_amb_impost'], 147.105 * 1.03
        )
        self.assertEqual(result['iva'], 3)
        self.assertEqual(result['ie'], 0)


class TestIndexedEstimationHelpers(unittest.TestCase):

    def setUp(self):
        self.pol = mock.Mock()
        self.models = {}
        self.pol.pool.get.side_effect = self.models.setdefault
        for model in ['res.config', 'ir.model.data', 'product.product',
                      'product.pricelist', 'account.tax', 'account.fiscal.position']:
            self.models[model] = mock.Mock()
        self.config = {
            'invoice_active_bo_social': '1',
            'invoice_start_date_bo_social': '2024-01-01',
            'giscedata_exclude_tariff_apply_bo_social': '[]',
        }
        self.models['res.config'].get.side_effect = (
            lambda cursor, uid, key, default=None: self.config.get(key, default)
        )
        self.pol.tarifa.name = '2.0TD'
        self.context = {'date': '2026-01-01'}

    def test_social_charge_uses_date_pricelist_and_product_taxes(self):
        self.models['ir.model.data'].get_object_reference.side_effect = [
            ('product', 42), ('uom', 43)
        ]
        self.models['product.pricelist'].price_get.return_value = {17: 0.02}
        product = self.models['product.product'].browse.return_value
        ctx = dict(self.context, force_pricelist=17)
        with mock.patch.object(utils, 'compute_estimation_taxes',
                               return_value=(8.833, {'IVA': 0.21})) as compute:
            result = utils.get_bo_social_estimation(None, 1, self.pol, context=ctx)
        self.assertNotIn('uom', ctx)
        price_context = dict(ctx, uom=43)
        self.assertAlmostEqual(result[0], 7.3)
        self.assertAlmostEqual(result[1], 8.833)
        compute.assert_called_once_with(
            None, 1, self.pol, 7.3, taxes=product.taxes_id,
            context=price_context, product=product
        )
        self.models['product.pricelist'].price_get.assert_called_once_with(
            None, 1, [17], 42, 1, context=price_context
        )

    def test_social_charge_disabled_before_start_or_excluded(self):
        for key, value in [
                ('invoice_active_bo_social', '0'),
                ('invoice_start_date_bo_social', '2027-01-01'),
                ('giscedata_exclude_tariff_apply_bo_social', "['2.0TD']")]:
            previous = self.config[key]
            self.config[key] = value
            self.assertEqual(
                utils.get_bo_social_estimation(None, 1, self.pol, context=self.context),
                (0, 0)
            )
            self.config[key] = previous
        self.assertFalse(self.models['product.pricelist'].price_get.called)

    def test_removed_product_taxes_do_not_fall_back_to_energy_defaults(self):
        self.models['account.fiscal.position'].map_tax.return_value = []
        self.models['account.tax'].browse.return_value = []
        self.models['account.tax'].compute.return_value = []
        total, rates = taxes.compute_estimation_taxes(
            None, 1, self.pol, 10, taxes=[], context=self.context
        )
        self.assertEqual((total, rates), (10, {}))
        self.assertFalse(self.models['res.config'].get.called)

    def test_engine_amounts_and_effective_rates_are_used(self):
        self.models['account.fiscal.position'].map_tax.return_value = [1, 2]
        ie = mock.Mock(factor=0, sequence=1, child_depend=False, include_base_amount=True)
        ie.name = 'IE exempt'
        igic = mock.Mock(factor=1, sequence=2, child_depend=False, include_base_amount=False)
        igic.name = 'IGIC 3%'
        self.models['account.tax'].browse.return_value = [igic, ie]
        self.models['account.tax'].compute.side_effect = [
            [{'amount': 0}], [{'amount': 3}],
        ]
        total, rates = taxes.compute_estimation_taxes(
            None, 1, self.pol, 100, taxes=[mock.Mock()], context=self.context
        )
        self.assertEqual(total, 103)
        self.assertEqual(rates, {'IE': 0, 'IGIC': 0.03})
        self.assertEqual(self.models['account.tax'].compute.call_args_list[0][0][3], 0)

    def test_draft_fiscal_policy_does_not_require_modcons(self):
        pol_obj = mock.Mock()
        pol_obj.read.return_value = {'state': 'esborrany'}
        context = {'date': datetime(2026, 1, 1)}
        taxes.get_tax_polissa(None, 1, pol_obj, 17, context=context)
        pol_obj.browse.assert_called_once_with(None, 1, 17, context={})
        self.assertIsInstance(context['date'], datetime)

    def test_active_fiscal_policy_uses_normalized_date(self):
        pol_obj = mock.Mock()
        pol_obj.read.return_value = {'state': 'activa'}
        taxes.get_tax_polissa(
            None, 1, pol_obj, 17, context={'date': datetime(2026, 1, 1)}
        )
        pol_obj.browse.assert_called_once_with(
            None, 1, 17, context={'date': '2026-01-01'}
        )
