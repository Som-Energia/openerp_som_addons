# -*- coding: utf-8 -*-
from __future__ import absolute_import

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

        self.assertEqual(result, (False, 'no_data'))

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

        self.assertEqual(result, ({
            'P1': 120,
            'P2': 60,
        }, 'full_data'))

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

        self.assertEqual(result, ({
            'P1': 132,
            'P2': 36,
        }, 'partial_data'))

    def _estimate_with_invoice_periods(self, contract_periods, invoice_periods):
        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        polissa = mock.Mock()
        polissa.tarifa.get_periodes.return_value = dict.fromkeys(
            ['P{}'.format(p) for p in range(1, contract_periods + 1)])
        lines = []
        for month, num_periods in enumerate(invoice_periods, 1):
            line = mock.Mock()
            invoice = line.factura_id
            invoice.tarifa_acces_id.id = num_periods
            invoice.tarifa_acces_id.get_periodes.return_value = dict.fromkeys(
                ['P{}'.format(p) for p in range(1, num_periods + 1)])
            invoice.invoice_id.date_invoice = '2016-{:02d}-15'.format(month)
            invoice.type = 'out_invoice'
            # GKWH need not be present in every period of the invoice tariff.
            line.factura_line_id.product_id.name = 'P1'
            line.factura_line_id.quantity = 10
            lines.append(line)

        owner = self.pool.get('generationkwh.invoice.line.owner')
        with mock.patch.object(self.Polissa, 'browse', return_value=polissa):
            with mock.patch.object(owner, 'browse', return_value=lines):
                return self.Polissa.generationkwh_anual_estimation(
                    self.cursor, self.uid, polissa_id, '2016-12-31')

    def test_generationkwh_anual_estimation_from_three_to_six_periods(self):
        result = self._estimate_with_invoice_periods(6, [3] * 8 + [6] * 4)

        self.assertEqual(result, ({'P1': 120}, 'partial_data'))

    def test_generationkwh_anual_estimation_from_six_to_three_periods(self):
        result = self._estimate_with_invoice_periods(3, [6] * 8 + [3] * 4)

        self.assertEqual(result, ({'P1': 120}, 'partial_data'))

    def test_generationkwh_anual_estimation_without_compatible_invoices(self):
        result = self._estimate_with_invoice_periods(3, [6] * 12)

        self.assertEqual(result, (False, 'no_data'))

    def test_generationkwh_anual_estimation_with_missing_gkwh_periods(self):
        result = self._estimate_with_invoice_periods(6, [6] * 12)

        self.assertEqual(result, ({'P1': 120}, 'full_data'))
