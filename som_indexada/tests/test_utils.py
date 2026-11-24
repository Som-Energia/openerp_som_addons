# -*- coding: utf-8 -*-
from __future__ import absolute_import, division

import unittest

import mock
from som_indexada import utils


class TestCalculateNewIndexedPrices(unittest.TestCase):

    def _calculate_prices(self, old_factor, new_factor, factor_change=None):
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
        with mock.patch.object(utils, 'get_preus', side_effect=prices):
            with mock.patch.object(
                utils, 'get_fs_from_k_change', return_value=factor_change or {}
            ):
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

    def test_integer_pricelist_factors_keep_fractional_kwh_values(self):
        result = self._calculate_prices(5, 7)

        self.assertAlmostEqual(result['f_antiga_kwh'], 0.005)
        self.assertAlmostEqual(result['f_nova_kwh'], 0.007)
        self._assert_estimation(result, 105.075, 107.105)

    def test_integer_factor_changes_override_pricelist_without_truncation(self):
        result = self._calculate_prices(5, 7, {'k_old': 11, 'k_new': 13})

        self.assertAlmostEqual(result['f_antiga_kwh'], 0.011)
        self.assertAlmostEqual(result['f_nova_kwh'], 0.013)
        self._assert_estimation(result, 111.165, 113.195)

    def test_float_factors_keep_existing_estimation(self):
        result = self._calculate_prices(5.5, 7.25)

        self.assertAlmostEqual(result['f_antiga_kwh'], 0.0055)
        self.assertAlmostEqual(result['f_nova_kwh'], 0.00725)
        self._assert_estimation(result, 105.5825, 107.35875)
