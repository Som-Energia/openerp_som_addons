# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from datetime import date, timedelta

from destral import testing
from destral.transaction import Transaction
from mock import Mock, patch
from som_indexada import utils as indexed_utils

from .. import report_backend_mailcanvipreus as backend_module


class TestPriceChangeCalculations(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor, self.uid = self.txn.cursor, self.txn.user
        self.backend = self.openerp.pool.get('report.backend.mailcanvipreus.pdf')
        self.pol = Mock(mode_facturacio='atr', llista_preu=Mock())
        self.pol.modcontractuals_ids = [Mock(state='actiu')]

    def tearDown(self):
        self.txn.stop()

    def test_energy_power_social_bonus_and_rounding_regression(self):
        prices = {'tp': 10.0, 'te': 0.1}
        contexts = []

        def atr_price(cursor, uid, pol, period, term, context=None, with_taxes=False):
            contexts.append(dict(context))
            return [prices[term]]

        context = {'date': '2026-10-01', 'price_change_old_price_date': '2026-09-30',
                   'price_change_effective_date': '2026-10-01'}
        with patch.object(backend_module, 'get_atr_price', side_effect=atr_price):
            with patch.object(self.backend, 'get_bo_social_price', return_value=6.0):
                result = self.backend.calcularPreuTotal(
                    self.cursor, self.uid, self.pol, {'P1': 100}, {'P1': 3},
                    False, True, date='2026-09-30', context=context)
        # Existing arithmetic: sum(price * quantity) plus annual social bonus.
        self.assertAlmostEqual(result, 10.0 * 3 + 0.1 * 100 + 6.0)
        self.assertTrue(all(item['date'] == '2026-09-30' for item in contexts))
        self.assertEqual(context['date'], '2026-10-01')
        original_taxes = getattr(self.backend, 'simplified_taxes', None)
        try:
            for taxes in ({'IVA': 0.21, 'IE': 0.0511}, {'IGIC': 0.03, 'IE': 0.0511},
                          {'IVA': 0.10, 'IE': 0.005}):
                self.backend.simplified_taxes = taxes
                iva = taxes.get('IVA', taxes.get('IGIC'))
                expected = round(round(result * (1 + taxes['IE']), 2) * (1 + iva))
                self.assertEqual(self.backend.calc_tax_for_anual_estimation(result), expected)
        finally:
            self.backend.simplified_taxes = original_taxes

    def test_generation_keeps_service_adjustment_and_excludes_social_bonus(self):
        conf_obj = self.openerp.pool.get('res.config')
        with patch.object(conf_obj, 'get', return_value='0.01'):
            with patch.object(backend_module, 'get_atr_price', return_value=[0.1]):
                with patch.object(self.backend, 'get_bo_social_price', return_value=6.0):
                    result = self.backend.calcularPreuTotal(
                        self.cursor, self.uid, self.pol, {'P1': 100}, {}, True, False,
                        date='2026-10-01', is_gkwh=True, context={})
        self.assertAlmostEqual(result, 100 * (0.1 + 0.01))

    def test_explicit_effective_date_wins_over_future_pricelist_and_clock(self):
        self.pol.llista_preu.version_id = [Mock(active=True, date_start='2099-01-01')]
        self.assertEqual(self.backend.get_price_change_date(
            self.cursor, self.uid, self.pol, {'price_change_effective_date': '2026-10-01'}),
            '2026-10-01')
        self.assertEqual(self.backend.get_price_change_date(
            self.cursor, self.uid, self.pol, {}), '2099-01-01')

    def test_indexed_prices_share_explicit_dates_and_campaign_fiscal_mapping(self):
        self.pol.cups.conany_kwh = 1000
        self.pol.tarifa.name = '2.0TD'
        self.pol.potencia = 3
        period = Mock(potencia=3)
        period.periode_id.name = 'P1'
        self.pol.potencies_periode = [period]
        self.pol.pool = self.openerp.pool
        config_obj = self.openerp.pool.get('res.config')
        contexts = []

        def prices(cursor, uid, pol, with_taxes=False, context=None):
            contexts.append(dict(context))
            if len(contexts) % 2:
                return {'tp': {'P1': 10.0}, 'factor_k': 11.2}
            return {'tp': {'P1': 9.5}, 'factor_k': 10.1}

        context = {'price_change_old_price_date': '2026-09-30',
                   'price_change_effective_date': '2026-10-01'}
        with patch.object(config_obj, 'get',
                          return_value="{'2.0TD': {'preu_sense_F': 100.0}}"):
            with patch.object(indexed_utils, 'get_preus', side_effect=prices):
                with patch.object(indexed_utils, 'get_fs_from_k_change', return_value={}):
                    legacy = indexed_utils.calculate_new_indexed_prices(
                        self.cursor, self.uid, self.pol, context=context)
                    mapped = indexed_utils.calculate_new_indexed_prices(
                        self.cursor, self.uid, self.pol, context=dict(
                            context, price_change_taxes={'IGIC': 0.03, 'IE': 0.0511}))
        self.assertEqual(contexts[0]['date'], '2026-09-30')
        self.assertEqual(contexts[1]['date'], '2026-10-01')
        old = (1.015 * 11.2 + 100.0) + 3 * 10.0
        new = (1.015 * 10.1 + 100.0) + 3 * 9.5
        self.assertIsInstance(legacy['iva'], int)
        self.assertAlmostEqual(legacy['import_total_anual_antiga'], old)
        self.assertAlmostEqual(legacy['import_total_anual_nova'], new)
        self.assertAlmostEqual(legacy['import_total_anual_antiga_amb_impost'], old * 1.0511 * 1.21)
        self.assertAlmostEqual(mapped['import_total_anual_antiga_amb_impost'], old * 1.0511 * 1.03)
        self.assertAlmostEqual(mapped['import_total_anual_nova_amb_impost'], new * 1.0511 * 1.03)

    def test_campaign_formatting_uses_the_same_decimal_paths_as_historical_data(self):
        backend = self.openerp.pool.get('report.backend.mailcanvipreus')
        record = Mock(_context={'lang': 'en_US'})
        data = {'preus_nous': {'te': {'P1': 0.123456}},
                'preu_nou': 358.7654, 'preu_auto_nou': 0.0345678}
        old = backend.format_return(self.cursor, self.uid, record, 'get_data', data, context={})
        new = backend.format_return(
            self.cursor, self.uid, record, 'get_campaign_data', data, context={})
        self.assertEqual(new, old)
        self.assertEqual(new['preus_nous']['te']['P1'], '0.123')
        self.assertEqual(new['preu_nou'], '359')
        self.assertEqual(new['preu_auto_nou'], '0.035')

    def test_legacy_new_prices_keep_sixty_day_default_without_a_future_version(self):
        self.pol.llista_preu.version_id = []
        self.assertEqual(self.backend.get_price_change_date(
            self.cursor, self.uid, self.pol, {}),
            (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'))
