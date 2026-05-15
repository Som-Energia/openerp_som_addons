# -*- coding: utf-8 -*-

from destral import testing
from osv import osv


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
