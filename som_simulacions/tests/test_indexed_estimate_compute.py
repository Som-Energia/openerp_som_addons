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

    def _create_request(self, tariff_code='2.0TD'):
        return self.request_obj.create(self.cursor, self.uid, {
            'name': 'REQ-001',
            'year': 2026,
            'month': 5,
            'tariff_code': tariff_code,
            'power_p1': 6.9,
            'power_p2': 4.6,
            'power_p3': 3.45,
        })

    def _create_request_payload(self, tariff_code='2.0TD'):
        return {
            'name': 'REQ-001',
            'year': 2026,
            'month': 5,
            'tariff_code': tariff_code,
            'power_p1': 6.9,
            'power_p2': 4.6,
            'power_p3': 3.45,
        }

    def _create_coeffs(self, tariff_code='2.0TD'):
        data = [
            ('P1', 0.5),
            ('P2', 0.3),
            ('P3', 0.2),
        ]
        for period, ratio in data:
            self.coeff_obj.create(self.cursor, self.uid, {
                'name': 'Coeff %s' % period,
                'year': 2026,
                'period': period,
                'tariff_code': tariff_code,
                'ratio': ratio,
            })

    def _create_prices(self, tariff_code='2.0TD'):
        data = [
            ('P1', 0.11),
            ('P2', 0.09),
            ('P3', 0.07),
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

    def test_compute_indexed_estimate_creates_result_and_lines(self):
        req_id = self._create_request()
        self._create_coeffs()
        self._create_prices()

        def fake_value(value, source='tariff', record_id=1):
            return {
                'value': value,
                'source': source,
                'record_id': record_id,
                'fallback_used': source != 'tariff',
            }

        self.adapter_obj.get_power_price = (
            lambda cr, uid, when_date, tariff_code=None, context=None: fake_value(20.0)
        )
        self.adapter_obj.get_social_bonus = (
            lambda cr, uid, when_date, tariff_code=None, context=None: fake_value(2.5)
        )
        self.adapter_obj.get_meter_charge = (
            lambda cr, uid, when_date, tariff_code=None, context=None: fake_value(1.5)
        )

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
        req_id = self._create_request()
        self._create_coeffs()
        self.price_obj.create(self.cursor, self.uid, {
            'name': 'Price P1',
            'year': 2026,
            'month': 5,
            'period': 'P1',
            'tariff_code': '2.0TD',
            'price': 0.11,
        })
        self.price_obj.create(self.cursor, self.uid, {
            'name': 'Price P2',
            'year': 2026,
            'month': 5,
            'period': 'P2',
            'tariff_code': '2.0TD',
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
