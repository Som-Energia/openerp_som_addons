# -*- coding: utf-8 -*-

from destral import testing
from osv.orm import FieldsValidationException


class TestIndexedEstimateModels(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestIndexedEstimateModels, self).setUp()
        self.pool = self.openerp.pool

    def test_model_registry_contains_indexed_estimate_models(self):
        expected_models = [
            'som.simulacio.energy.price.monthly',
            'som.simulacio.annual.coeff',
            'som.simulacio.request',
            'som.simulacio.result',
            'som.simulacio.result.line',
            'som.simulacio.erp.adapter',
        ]
        for model_name in expected_models:
            self.assertTrue(self.pool.get(model_name), model_name)

    def test_energy_price_and_coeff_models_define_expected_constraints(self):
        price_model = self.pool.get('som.simulacio.energy.price.monthly')
        coeff_model = self.pool.get('som.simulacio.annual.coeff')

        price_constraint = [c for c in price_model._sql_constraints if c[0]
                            == 'uniq_monthly_tariff_period']
        coeff_constraint = [c for c in coeff_model._sql_constraints if c[0]
                            == 'uniq_annual_tariff_period']

        self.assertTrue(price_constraint)
        self.assertIn('year, month, period, tariff_code', price_constraint[0][1])
        self.assertTrue(coeff_constraint)
        self.assertIn('year, period, tariff_code', coeff_constraint[0][1])

    def test_simulation_result_has_traceability_fields(self):
        result_model = self.pool.get('som.simulacio.result')
        self.assertIn('selected_energy_price_id', result_model._columns)
        self.assertIn('selected_coeff_set_id', result_model._columns)
        self.assertIn('fallback_flags', result_model._columns)

    def test_adapter_exposes_old_api_methods(self):
        adapter = self.pool.get('som.simulacio.erp.adapter')
        self.assertTrue(hasattr(adapter, 'get_power_price'))
        self.assertTrue(hasattr(adapter, 'get_social_bonus'))
        self.assertTrue(hasattr(adapter, 'get_meter_charge'))

    def test_energy_price_requires_positive_price(self):
        price_model = self.pool.get('som.simulacio.energy.price.monthly')

        self.assertRaises(
            FieldsValidationException,
            price_model.create,
            self.cursor,
            self.uid,
            {
                'name': 'Invalid price',
                'year': 2026,
                'month': 6,
                'period': 'P1',
                'tariff_code': '2.0TD',
                'price': 0.0,
            },
        )

    def test_energy_price_rejects_duplicate_year_month_period_tariff(self):
        price_model = self.pool.get('som.simulacio.energy.price.monthly')
        values = {
            'name': 'Price unique key',
            'year': 2031,
            'month': 7,
            'period': 'P1',
            'tariff_code': '2.0TD',
            'price': 0.11,
        }
        price_model.create(self.cursor, self.uid, values)

        self.assertRaises(
            Exception,
            price_model.create,
            self.cursor,
            self.uid,
            dict(values, name='Price duplicate'),
        )

    def test_annual_coeff_rejects_ratio_out_of_range(self):
        coeff_model = self.pool.get('som.simulacio.annual.coeff')

        self.assertRaises(
            FieldsValidationException,
            coeff_model.create,
            self.cursor,
            self.uid,
            {
                'name': 'Coeff invalid',
                'year': 2027,
                'period': 'P1',
                'tariff_code': '2.0TD',
                'ratio': 1.2,
                'date_from': '2027-01-01',
                'date_to': '2027-12-31',
            },
        )

    def test_annual_coeff_rejects_sum_different_from_one(self):
        coeff_model = self.pool.get('som.simulacio.annual.coeff')
        coeff_model.create(self.cursor, self.uid, {
            'name': 'Coeff P1',
            'year': 2028,
            'period': 'P1',
            'tariff_code': '2.0TD',
            'ratio': 0.6,
            'date_from': '2028-01-01',
            'date_to': '2028-12-31',
        })
        coeff_model.create(self.cursor, self.uid, {
            'name': 'Coeff P2',
            'year': 2028,
            'period': 'P2',
            'tariff_code': '2.0TD',
            'ratio': 0.3,
            'date_from': '2028-01-01',
            'date_to': '2028-12-31',
        })

        self.assertRaises(
            FieldsValidationException,
            coeff_model.create,
            self.cursor,
            self.uid,
            {
                'name': 'Coeff P3 invalid total',
                'year': 2028,
                'period': 'P3',
                'tariff_code': '2.0TD',
                'ratio': 0.05,
                'date_from': '2028-01-01',
                'date_to': '2028-12-31',
            },
        )

    def test_annual_coeff_rejects_overlapping_window_same_period_tariff(self):
        coeff_model = self.pool.get('som.simulacio.annual.coeff')
        coeff_model.create(self.cursor, self.uid, {
            'name': 'Coeff 1',
            'year': 2029,
            'period': 'P1',
            'tariff_code': '2.0TD',
            'ratio': 0.4,
            'date_from': '2029-01-01',
            'date_to': '2029-06-30',
        })

        self.assertRaises(
            FieldsValidationException,
            coeff_model.create,
            self.cursor,
            self.uid,
            {
                'name': 'Coeff overlap',
                'year': 2030,
                'period': 'P1',
                'tariff_code': '2.0TD',
                'ratio': 0.4,
                'date_from': '2029-06-01',
                'date_to': '2030-12-31',
            },
        )

    def test_annual_coeff_rejects_duplicate_year_period_tariff(self):
        coeff_model = self.pool.get('som.simulacio.annual.coeff')
        values = {
            'name': 'Coeff unique key',
            'year': 2032,
            'period': 'P1',
            'tariff_code': '2.0TD',
            'ratio': 0.4,
            'date_from': '2032-01-01',
            'date_to': '2032-12-31',
        }
        coeff_model.create(self.cursor, self.uid, values)

        self.assertRaises(
            Exception,
            coeff_model.create,
            self.cursor,
            self.uid,
            dict(values, name='Coeff duplicate'),
        )
