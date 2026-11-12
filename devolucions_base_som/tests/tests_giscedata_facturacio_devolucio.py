# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import mock
from devolucions_base.tests import TestsDevolucions
from destral.transaction import Transaction
from destral.patch import PatchNewCursors


class TestsDevolucioPaidFlag(TestsDevolucions):

    @mock.patch('remeses_base.payment.PaymentOrder.check_order_paid')
    def test_check_order_paid_is_called_after_devolucio_processed(self, mock_check_order_paid):
        config_obj = self.openerp.pool.get('res.config')
        dev_obj = self.openerp.pool.get('giscedata.facturacio.devolucio')
        conf_obj = self.openerp.pool.get('res.config')
        mock_check_order_paid.return_value = None

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            with PatchNewCursors():
                self._init_services(cursor, uid)
                context = {}
                vals = self.crear_devolucion_factura(cursor, uid)
                linia_2 = vals['linia_2']
                invoice_2 = vals['invoice_2']
                invoice_2_id = vals['invoice_2_id']
                devolucio_id = vals['devolucio_id']
                config_id = config_obj.search(
                    cursor, uid, [("name", "=", "devolucio_moviment_unic")])
                config_obj.write(cursor, uid, config_id[0], {'value': True}, context=context)
                self.make_payment(cursor, uid, invoice_2.amount_total, invoice_2_id)
                conf_obj.set(cursor, uid, 'despeses_devolucio', '0')

                dev_obj.process_devolucio_lines_moviment_unic(
                    cursor, uid, devolucio_id, [linia_2.id], True, context=context)

                mock_check_order_paid.assert_called_once_with(cursor, uid, [1], context=context)
