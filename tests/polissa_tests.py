# -*- coding: utf-8 -*-
import mock
from destral import testing


class PolissaTests(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(PolissaTests, self).setUp()
        self.pool = self.openerp.pool
        self.IrModelData = self.pool.get('ir.model.data')
        self.Polissa = self.pool.get('giscedata.polissa')

    def test_get_generationkwh_use(self):
        cursor = self.cursor
        uid = self.uid

        polissa_id = self.IrModelData.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        result = self.Polissa.get_generationkwh_use(
            cursor, uid, polissa_id, '2016-01-01', '2016-12-31')

        self.assertEqual(result['2016-03-01']['P1'], 1)

    @mock.patch("som_generationkwh.giscedata_polissa.GiscedataPolissa.get_generationkwh_use")
    def test_generationkwh_anual_estimation_with_no_data(self, mocked_get_use):
        cursor = self.cursor
        uid = self.uid

        mocked_get_use.return_value = False

        polissa_id = self.IrModelData.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        result = self.Polissa.generationkwh_anual_estimation(
            cursor, uid, polissa_id, '2016-12-31')

        self.assertFalse(result)

    @mock.patch("som_generationkwh.giscedata_polissa.GiscedataPolissa.get_generationkwh_use")
    def test_generationkwh_anual_estimation_with_full_data(self, mocked_get_use):
        cursor = self.cursor
        uid = self.uid

        mocked_get_use.return_value = {
            '2016-{:02d}-15'.format(month): {
                'P1': 10,
                'P2': 5,
            } for month in range(1, 13)
        }

        polissa_id = self.IrModelData.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        result = self.Polissa.generationkwh_anual_estimation(
            cursor, uid, polissa_id, '2016-12-31')

        self.assertEqual(result, {
            'P1': 120,
            'P2': 60,
        })


    @mock.patch("som_generationkwh.giscedata_polissa.GiscedataPolissa.get_generationkwh_use")
    def test_generationkwh_anual_estimation_with_partial_data(self, mocked_get_use):
        cursor = self.cursor
        uid = self.uid

        mocked_get_use.return_value = {
            '2016-11-15': {
                'P1': 10,
                'P2': 2,
            },
            '2016-12-15': {
                'P1': 12,
                'P2': 4,
            },
        }

        polissa_id = self.IrModelData.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        result = self.Polissa.generationkwh_anual_estimation(
            cursor, uid, polissa_id, '2016-12-31')

        self.assertEqual(result, {
            'P1': 132,
            'P2': 36,
        })