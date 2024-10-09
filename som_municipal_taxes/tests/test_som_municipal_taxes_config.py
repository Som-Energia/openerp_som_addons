# -*- coding: utf-8 -*-

from destral import testing
import mock
from giscedata_facturacio.facturacio_extra import FacturacioExtra


class TestSomMunicipalTaxesConfig(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestSomMunicipalTaxesConfig, self).setUp()
        self.pool = self.openerp.pool

    def test_generate_municipal_taxes_file_path_no_municipis(self):
        imd_obj = self.openerp.pool.get('ir.model.data')
        municipal_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'base_extended',
            'ine_01001'
        )[1]
        config_o = self.pool.get('som.municipal.taxes.config')
        context = {
            'any': 2024,
            'trimestre': 1,
        }

        result = config_o.generate_municipal_taxes_file_path(
            self.cursor, self.uid, [], municipal_id, context)

        self.assertFalse(result)

    @mock.patch.object(FacturacioExtra, "get_states_invoiced")
    def test_generate_municipal_taxes_file_path_ok(self, get_states_invoiced_mock):
        get_states_invoiced_mock.return_value = ['draft', 'open', 'paid']
        imd_obj = self.openerp.pool.get('ir.model.data')
        municipal_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'base_extended',
            'ine_01001'
        )[1]
        config_o = self.pool.get('som.municipal.taxes.config')
        context = {
            'any': 2016,
            'trimestre': 1,
        }

        result = config_o.generate_municipal_taxes_file_path(
            self.cursor, self.uid, [], municipal_id, context)

        self.assertEqual(result, '/tmp/municipal_taxes_1.xlsx')
