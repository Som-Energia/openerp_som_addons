# -*- coding: utf-8 -*-

from destral import testing
from osv import osv
import ast


class TestIndexedEstimateCompute(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestIndexedEstimateCompute, self).setUp()
        self.pool = self.openerp.pool
        self.request_obj = self.pool.get('som.simulacio.request')
        self.price_obj = self.pool.get('som.simulacio.energy.price.monthly')
        self.coeff_obj = self.pool.get('som.simulacio.annual.coeff')
        self.result_obj = self.pool.get('som.simulacio.result')
        self.adapter_obj = self.pool.get('som.simulacio.erp.adapter')

    def _create_request(self, tariff_code='2.0TD_TEST'):
        return self.request_obj.create(self.cursor, self.uid, {
            'name': 'REQ-001',
            'year': 2026,
            'month': 5,
            'tariff_code': tariff_code,
            'power_p1': 6.9,
            'power_p2': 4.6,
            'power_p3': 3.45,
        })

    def _create_request_payload(self, tariff_code='2.0TD_TEST'):
        return {
            'name': 'REQ-001',
            'year': 2026,
            'month': 5,
            'tariff_code': tariff_code,
            'power_p1': 6.9,
            'power_p2': 4.6,
            'power_p3': 3.45,
        }

    def _create_coeffs(self, tariff_code='2.0TD_TEST'):
        data = [
            ('P1', 0.26),
            ('P2', 0.28),
            ('P3', 0.46),
        ]
        for period, ratio in data:
            self.coeff_obj.create(self.cursor, self.uid, {
                'name': 'Coeff %s' % period,
                'year': 2026,
                'period': period,
                'tariff_code': tariff_code,
                'ratio': ratio,
            })

    def _create_prices(self, tariff_code='2.0TD_TEST'):
        data = [
            ('P1', 0.235463),
            ('P2', 0.140257),
            ('P3', 0.111906),
        ]
        for period, price in data:
            self.price_obj.create(self.cursor, self.uid, {
                'name': 'Price %s' % period,
                'year': 2026,
                'month': 5,
                'period': period,
                'tariff_code': tariff_code,
                'price': price,
            })

    def _fake_csv_adapter(self):
        self.adapter_obj.get_power_price = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 0.0,
                'components': {'p1': 29.934, 'p2': 2.955},
                'source': 'tariff',
                'record_id': 1,
                'fallback_used': False,
            }
        )
        self.adapter_obj.get_social_bonus = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 0.81,
                'source': 'tariff',
                'record_id': 2,
                'fallback_used': False,
            }
        )
        self.adapter_obj.get_meter_charge = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 0.5816,
                'source': 'tariff',
                'record_id': 3,
                'fallback_used': False,
            }
        )

    def test_compute_indexed_estimate_creates_result_and_lines(self):
        req_id = self._create_request()
        self._create_coeffs()
        self._create_prices()
        self._fake_csv_adapter()

        result_ids = self.request_obj.compute_indexed_estimate(
            self.cursor, self.uid, [req_id], context=None)
        self.assertEqual(1, len(result_ids))

        result = self.result_obj.read(
            self.cursor, self.uid, result_ids[0],
            ['untaxed_total', 'traceability_payload', 'fallback_flags', 'line_ids']
        )
        self.assertTrue(result['untaxed_total'] > 0.0)
        self.assertTrue(result['traceability_payload'])
        self.assertTrue(result['fallback_flags'])
        self.assertEqual(6, len(result['line_ids']))

    def test_adapter_fallback_order_tariff_then_default_then_error(self):
        calls = []

        def tariff_stub(cr, uid, concept_name, when_date, tariff_code=None, context=None):
            calls.append('tariff')
            return None

        def default_stub(cr, uid, concept_name, when_date, context=None):
            calls.append('default')
            return {'value': 3.0, 'record_id': 77}

        self.adapter_obj._get_tariff_specific_value = tariff_stub
        self.adapter_obj._get_company_default_value = default_stub

        val = self.adapter_obj.get_meter_charge(
            self.cursor, self.uid, '2026-05-01', tariff_code='2.0TD', context=None
        )
        self.assertEqual(['tariff', 'default'], calls)
        self.assertEqual(3.0, val['value'])
        self.assertEqual('default', val['source'])
        self.assertTrue(val['fallback_used'])

        def no_default_stub(cr, uid, concept_name, when_date, context=None):
            return None

        self.adapter_obj._get_company_default_value = no_default_stub

        self.assertRaises(
            osv.except_osv,
            self.adapter_obj.get_meter_charge,
            self.cursor,
            self.uid,
            '2026-05-01',
            '2.0TD',
            None,
        )

    def test_adapter_returns_power_components_from_tariff_products(self):
        original_tariff = self.adapter_obj._get_tariff_specific_value
        self.adapter_obj._get_tariff_specific_value = (
            lambda cr, uid, concept_name, when_date, tariff_code=None, context=None: {
                'value': 0.0,
                'components': {'p1': 29.934, 'p2': 2.955},
                'record_id': 55,
            }
        )
        try:
            val = self.adapter_obj.get_power_price(
                self.cursor, self.uid, '2026-05-01', tariff_code='2.0TD', context=None
            )
        finally:
            self.adapter_obj._get_tariff_specific_value = original_tariff

        self.assertEqual('tariff', val['source'])
        self.assertFalse(val['fallback_used'])
        self.assertEqual(55, val['record_id'])
        self.assertEqual(0.0, val['value'])
        self.assertEqual(29.934, val['components']['p1'])
        self.assertEqual(2.955, val['components']['p2'])

    def test_adapter_gets_social_bonus_from_tariff_product_reference(self):
        original_tariff = self.adapter_obj._get_tariff_specific_value
        self.adapter_obj._get_tariff_specific_value = (
            lambda cr, uid, concept_name, when_date, tariff_code=None, context=None: {
                'value': 0.81,
                'record_id': 201,
            }
        )
        try:
            val = self.adapter_obj.get_social_bonus(
                self.cursor, self.uid, '2026-05-01', tariff_code='2.0TD', context=None
            )
        finally:
            self.adapter_obj._get_tariff_specific_value = original_tariff

        self.assertEqual(0.81, val['value'])
        self.assertEqual('tariff', val['source'])
        self.assertEqual(201, val['record_id'])
        self.assertFalse(val['fallback_used'])

    def test_adapter_meter_charge_uses_default_when_tariff_lookup_missing(self):
        original_tariff_value = self.adapter_obj._get_tariff_product_value
        original_default_value = self.adapter_obj._get_company_default_value

        self.adapter_obj._get_tariff_product_value = (
            lambda cr, uid, when_date, tariff_code, xml_or_code,
            use_default_code=False, context=None: None
        )
        self.adapter_obj._get_company_default_value = (
            lambda cr, uid, concept_name, when_date, context=None: {
                'value': 0.5816,
                'record_id': 301,
            }
        )
        try:
            val = self.adapter_obj.get_meter_charge(
                self.cursor, self.uid, '2026-05-01', tariff_code='2.0TD', context=None
            )
        finally:
            self.adapter_obj._get_tariff_product_value = original_tariff_value
            self.adapter_obj._get_company_default_value = original_default_value

        self.assertEqual(0.5816, val['value'])
        self.assertEqual('default', val['source'])
        self.assertEqual(301, val['record_id'])
        self.assertTrue(val['fallback_used'])

    def test_compute_rejects_missing_tariff_context(self):
        payload = self._create_request_payload(tariff_code='')
        req_id = self.request_obj.create(self.cursor, self.uid, payload)

        self.assertRaises(
            osv.except_osv,
            self.request_obj.compute_indexed_estimate,
            self.cursor,
            self.uid,
            [req_id],
            None,
        )

    def test_compute_rejects_negative_power(self):
        payload = self._create_request_payload()
        payload['power_p2'] = -0.5
        req_id = self.request_obj.create(self.cursor, self.uid, payload)

        self.assertRaises(
            osv.except_osv,
            self.request_obj.compute_indexed_estimate,
            self.cursor,
            self.uid,
            [req_id],
            None,
        )

    def test_compute_rejects_when_all_powers_are_zero(self):
        payload = self._create_request_payload()
        payload.update({'power_p1': 0.0, 'power_p2': 0.0, 'power_p3': 0.0})
        req_id = self.request_obj.create(self.cursor, self.uid, payload)

        self.assertRaises(
            osv.except_osv,
            self.request_obj.compute_indexed_estimate,
            self.cursor,
            self.uid,
            [req_id],
            None,
        )

    def test_compute_rejects_missing_coefficients(self):
        req_id = self._create_request()
        self._create_prices()

        self.adapter_obj.get_power_price = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 10.0,
                'source': 'tariff',
                'record_id': 1,
                'fallback_used': False,
            }
        )
        self.adapter_obj.get_social_bonus = self.adapter_obj.get_power_price
        self.adapter_obj.get_meter_charge = self.adapter_obj.get_power_price

        self.assertRaises(
            osv.except_osv,
            self.request_obj.compute_indexed_estimate,
            self.cursor,
            self.uid,
            [req_id],
            None,
        )

    def test_compute_rejects_missing_monthly_price_for_required_period(self):
        req_id = self._create_request(tariff_code='2.0TD_MISSING')
        self._create_coeffs('2.0TD_MISSING')
        self.price_obj.create(self.cursor, self.uid, {
            'name': 'Price P1',
            'year': 2026,
            'month': 5,
            'period': 'P1',
            'tariff_code': '2.0TD_MISSING',
            'price': 0.11,
        })
        self.price_obj.create(self.cursor, self.uid, {
            'name': 'Price P2',
            'year': 2026,
            'month': 5,
            'period': 'P2',
            'tariff_code': '2.0TD_MISSING',
            'price': 0.09,
        })

        self.adapter_obj.get_power_price = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 10.0,
                'source': 'tariff',
                'record_id': 1,
                'fallback_used': False,
            }
        )
        self.adapter_obj.get_social_bonus = self.adapter_obj.get_power_price
        self.adapter_obj.get_meter_charge = self.adapter_obj.get_power_price

        self.assertRaises(
            osv.except_osv,
            self.request_obj.compute_indexed_estimate,
            self.cursor,
            self.uid,
            [req_id],
            None,
        )

    def test_compute_persists_fallback_traceability_sources(self):
        req_id = self._create_request()
        self._create_coeffs()
        self._create_prices()

        self.adapter_obj.get_power_price = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 20.0,
                'source': 'default',
                'record_id': 10,
                'fallback_used': True,
            }
        )
        self.adapter_obj.get_social_bonus = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 2.5,
                'source': 'tariff',
                'record_id': 11,
                'fallback_used': False,
            }
        )
        self.adapter_obj.get_meter_charge = (
            lambda cr, uid, when_date, tariff_code=None, context=None: {
                'value': 1.5,
                'source': 'tariff',
                'record_id': 12,
                'fallback_used': False,
            }
        )

        result_ids = self.request_obj.compute_indexed_estimate(
            self.cursor, self.uid, [req_id], context=None)
        result = self.result_obj.read(
            self.cursor, self.uid, result_ids[0],
            ['fallback_flags', 'traceability_payload']
        )

        fallback_flags = ast.literal_eval(result['fallback_flags'])
        traceability_payload = ast.literal_eval(result['traceability_payload'])

        self.assertTrue(fallback_flags['power_price'])
        self.assertFalse(fallback_flags['social_bonus'])
        self.assertEqual(
            'default', traceability_payload['concept_sources']['power_price'])
        self.assertEqual(
            'tariff', traceability_payload['concept_sources']['social_bonus'])

    def test_csv_row_parity_power_1(self):
        req_id = self.request_obj.create(self.cursor, self.uid, {
            'name': 'CSV-1',
            'year': 2026,
            'month': 5,
            'tariff_code': '2.0TD_CSV_A',
            'power_p1': 1.0,
            'power_p2': 1.0,
            'power_p3': 0.0,
        })
        self._create_coeffs('2.0TD_CSV_A')
        self._create_prices('2.0TD_CSV_A')
        self._fake_csv_adapter()

        result_id = self.request_obj.compute_indexed_estimate(
            self.cursor, self.uid, [req_id], context=None)[0]
        result = self.result_obj.read(
            self.cursor, self.uid, result_id, ['untaxed_total', 'traceability_payload', 'line_ids'])
        trace = ast.literal_eval(result['traceability_payload'])
        self.assertEqual(2500.0, trace['annual_kwh'])
        self.assertEqual(54, trace['period_kwh']['P1'])
        self.assertEqual(58, trace['period_kwh']['P2'])
        self.assertEqual(96, trace['period_kwh']['P3'])

        lines = self.pool.get('som.simulacio.result.line').read(
            self.cursor, self.uid, result['line_ids'], ['concept', 'period', 'amount'])
        energy_total = round(result['untaxed_total'] - 2.74 - 0.81 - 0.58, 2)
        power_total = [line['amount'] for line in lines if line['concept'] == 'power_price'][0]
        self.assertEqual(31.66, energy_total)
        self.assertEqual(2.74, round(power_total, 2))
        self.assertEqual(35.79, round(result['untaxed_total'], 2))

    def test_csv_row_parity_power_2(self):
        req_id = self.request_obj.create(self.cursor, self.uid, {
            'name': 'CSV-2',
            'year': 2026,
            'month': 5,
            'tariff_code': '2.0TD_CSV_B',
            'power_p1': 2.0,
            'power_p2': 2.0,
            'power_p3': 0.0,
        })
        self._create_coeffs('2.0TD_CSV_B')
        self._create_prices('2.0TD_CSV_B')
        self._fake_csv_adapter()

        result_id = self.request_obj.compute_indexed_estimate(
            self.cursor, self.uid, [req_id], context=None)[0]
        result = self.result_obj.read(
            self.cursor, self.uid, result_id, ['untaxed_total', 'traceability_payload', 'line_ids'])
        trace = ast.literal_eval(result['traceability_payload'])
        self.assertEqual(2750.0, trace['annual_kwh'])
        self.assertEqual(60, trace['period_kwh']['P1'])
        self.assertEqual(64, trace['period_kwh']['P2'])
        self.assertEqual(105, trace['period_kwh']['P3'])

        lines = self.pool.get('som.simulacio.result.line').read(
            self.cursor, self.uid, result['line_ids'], ['concept', 'period', 'amount'])
        energy_total = round(result['untaxed_total'] - 5.48 - 0.81 - 0.58, 2)
        power_total = [line['amount'] for line in lines if line['concept'] == 'power_price'][0]
        self.assertEqual(34.83, energy_total)
        self.assertEqual(5.48, round(power_total, 2))
        self.assertEqual(41.70, round(result['untaxed_total'], 2))

    def test_csv_row_parity_power_10(self):
        req_id = self.request_obj.create(self.cursor, self.uid, {
            'name': 'CSV-10',
            'year': 2026,
            'month': 5,
            'tariff_code': '2.0TD_CSV_C',
            'power_p1': 10.0,
            'power_p2': 10.0,
            'power_p3': 0.0,
        })
        self._create_coeffs('2.0TD_CSV_C')
        self._create_prices('2.0TD_CSV_C')
        self._fake_csv_adapter()

        result_id = self.request_obj.compute_indexed_estimate(
            self.cursor, self.uid, [req_id], context=None)[0]
        result = self.result_obj.read(
            self.cursor, self.uid, result_id, ['untaxed_total', 'traceability_payload', 'line_ids'])
        trace = ast.literal_eval(result['traceability_payload'])
        self.assertEqual(4750.0, trace['annual_kwh'])
        self.assertEqual(103, trace['period_kwh']['P1'])
        self.assertEqual(111, trace['period_kwh']['P2'])
        self.assertEqual(182, trace['period_kwh']['P3'])

        lines = self.pool.get('som.simulacio.result.line').read(
            self.cursor, self.uid, result['line_ids'], ['concept', 'period', 'amount'])
        energy_total = round(result['untaxed_total'] - 27.41 - 0.81 - 0.58, 2)
        power_total = [line['amount'] for line in lines if line['concept'] == 'power_price'][0]
        self.assertEqual(60.15, energy_total)
        self.assertEqual(27.41, round(power_total, 2))
        self.assertEqual(88.95, round(result['untaxed_total'], 2))
