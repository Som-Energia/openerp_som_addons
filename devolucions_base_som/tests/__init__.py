# -*- coding: utf-8 -*-
from destral import testing


class TestsDevolucioPaidFlag(testing.OOTestCaseWithCursor):

    def test_check_order_paid_is_called_after_devolucio_processed(self):
        devolucio_obj = self.openerp.pool.get('giscedata.facturacio.devolucio')
        payment_order_obj = self.openerp.pool.get('payment.order')

        with self.mock.patch.object(
            payment_order_obj, 'check_order_paid'
        ) as mock_check_order_paid:
            mock_check_order_paid.return_value = None

            devolucio_obj.process_devolucio_lines_moviment_unic(
                self.cursor, self.uid, 1, [1], 0, context={}
            )

            mock_check_order_paid.assert_called()
