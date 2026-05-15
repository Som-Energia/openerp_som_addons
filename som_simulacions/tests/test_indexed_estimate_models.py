# -*- coding: utf-8 -*-

from destral import testing


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
