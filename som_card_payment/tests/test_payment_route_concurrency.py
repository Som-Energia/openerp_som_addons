# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date
import threading

from destral import testing
import mock
import netsvc
from osv import osv
import pooler


class TestPaymentRouteConcurrency(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestPaymentRouteConcurrency, self).setUp()
        self.invoice_obj = self.openerp.pool.get('account.invoice')
        self.factura_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        self.order_obj = self.openerp.pool.get('payment.order')
        self.imd_obj = self.openerp.pool.get('ir.model.data')
        self.database_obj = pooler.get_db(self.cursor.dbname)
        self.card_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_card_payment', 'payment_type_card_recurrent'
        )[1]

    def _prepare_invoice_and_order(self):
        invoice_ids = self.invoice_obj.search(
            self.cursor, self.uid,
            [('type', '=', 'out_invoice'), ('state', '=', 'open'),
             ('payment_order_id', '=', False), ('residual', '>', 0)],
            limit=1,
        )
        self.assertTrue(invoice_ids)
        invoice_id = invoice_ids[0]
        original = self.invoice_obj.read(
            self.cursor, self.uid, invoice_id, ['date_due', 'payment_type', 'state']
        )
        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_tarifa_018'
        )[1]
        polissa = self.openerp.pool.get('giscedata.polissa').browse(
            self.cursor, self.uid, polissa_id
        )
        factura_id = self.factura_obj.create(self.cursor, self.uid, {
            'invoice_id': invoice_id,
            'polissa_id': polissa_id,
            'tarifa_acces_id': polissa.tarifa.id,
            'cups_id': polissa.cups.id,
            'llista_preu': polissa.llista_preu.id,
            'potencia': 1,
            'date_boe': '2021-01-01',
            'facturacio': 1,
        })
        mode_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'account_payment', 'payment_mode_demo'
        )[1]
        line_ids = self.invoice_obj.move_line_id_payment_get(
            self.cursor, self.uid, [invoice_id]
        )
        self.assertTrue(line_ids)
        line = self.openerp.pool.get('account.move.line').browse(
            self.cursor, self.uid, line_ids[0]
        )
        self.assertNotEqual(line.amount_to_pay, 0)
        mode_id = self.openerp.pool.get('payment.mode').copy(
            self.cursor, self.uid, mode_id,
            {'name': 'Concurrent payment route test',
             'tipo': 'sepa19' if line.amount_to_pay < 0 else 'sepa34'},
        )
        order_id = self.order_obj.create(self.cursor, self.uid, {
            'mode': mode_id,
            'type': 'receivable' if line.amount_to_pay < 0 else 'payable',
            'date_prefered': 'now',
            'create_account_moves': 'direct-payment',
        })
        self.invoice_obj.write(self.cursor, self.uid, [invoice_id], {
            'payment_type': False,
            'date_due': date.today().strftime('%Y-%m-%d'),
        })
        self.cursor.commit()
        self.addCleanup(
            self._clean_committed_fixture, factura_id, invoice_id, original, order_id, mode_id
        )
        return factura_id, invoice_id, polissa_id, order_id

    def _clean_committed_fixture(self, factura_id, invoice_id, original, order_id, mode_id):
        cursor = self.database_obj.cursor()
        try:
            self.invoice_obj.write(cursor, self.uid, [invoice_id], {
                'date_due': original['date_due'],
                'payment_type': original['payment_type'] and original['payment_type'][0],
                'payment_order_id': False,
            })
            for model_name, field_name in (
                ('payment.order.history', 'payment_order_id'),
                ('payment.line', 'order_id'),
            ):
                model = self.openerp.pool.get(model_name)
                record_ids = model.search(cursor, self.uid, [(field_name, '=', order_id)])
                model.unlink(cursor, self.uid, record_ids)
            self.order_obj.unlink(cursor, self.uid, [order_id])
            self.openerp.pool.get('payment.mode').unlink(cursor, self.uid, [mode_id])
            netsvc.LocalService('workflow').trg_delete(
                self.uid, 'giscedata.facturacio.factura', factura_id, cursor
            )
            # Unlinking the inherited factura would also delete the shared demo invoice.
            cursor.execute('DELETE FROM giscedata_facturacio_factura WHERE id = %s', (factura_id,))
            # Restoring an open state through write() would create pending-state history.
            cursor.execute(
                'UPDATE account_invoice SET state = %s WHERE id = %s',
                (original['state'], invoice_id),
            )
            cursor.commit()
        except Exception:
            cursor.rollback()
            raise
        finally:
            cursor.close()

    def _assert_routes_are_serialized(self, first_route, first_commits=True):
        factura_id, invoice_id, polissa_id, order_id = self._prepare_invoice_and_order()
        second_route = 'conversion' if first_route == 'remittance' else 'remittance'
        first_at_write = threading.Event()
        release_first = threading.Event()
        second_started = threading.Event()
        second_finished = threading.Event()
        results = {}
        errors = {}
        original_write = self.invoice_obj.write
        first_field = 'payment_order_id' if first_route == 'remittance' else 'payment_type'

        def pause_first_write(cursor, uid, ids, values, context=None):
            if invoice_id in ids and first_field in values:
                first_at_write.set()
                if not release_first.wait(10):
                    raise RuntimeError('Timed out waiting to release the first payment route')
            return original_write(cursor, uid, ids, values, context=context)

        def run_route(route):
            cursor = self.database_obj.cursor()
            try:
                cursor.execute("SET LOCAL statement_timeout = '15s'")
                if route == second_route:
                    second_started.set()
                if route == 'conversion':
                    results[route] = self.factura_obj.migrate_recurring_card_invoices(
                        cursor, self.uid, polissa_id, self.card_type_id,
                        date.today().strftime('%Y-%m-%d'), context={'lang': 'en_US'},
                    )
                else:
                    results[route] = self.invoice_obj.afegeix_a_remesa(
                        cursor, self.uid, [invoice_id], order_id, context={'lang': 'en_US'}
                    )
                if route == first_route and not first_commits:
                    cursor.rollback()
                else:
                    cursor.commit()
            except Exception as error:
                cursor.rollback()
                errors[route] = error
            finally:
                cursor.close()
                if route == second_route:
                    second_finished.set()

        first = threading.Thread(target=run_route, args=(first_route,))
        second = threading.Thread(target=run_route, args=(second_route,))
        with mock.patch.object(self.invoice_obj, 'write', side_effect=pause_first_write):
            try:
                first.start()
                self.assertTrue(first_at_write.wait(10), repr((results, errors)))
                second.start()
                self.assertTrue(second_started.wait(10))
                self.assertFalse(second_finished.wait(0.5), repr((results, errors)))
            finally:
                release_first.set()
                first.join(20)
                if second.ident is not None:
                    second.join(20)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertNotIn(first_route, errors)
        invoice = self.invoice_obj.read(
            self.cursor, self.uid, invoice_id, ['payment_type', 'payment_order_id']
        )
        remittance_wins = (first_route == 'remittance') == first_commits
        if remittance_wins:
            self.assertEqual(errors, {})
            self.assertFalse(invoice['payment_type'])
            self.assertEqual(invoice['payment_order_id'][0], order_id)
            if first_commits:
                self.assertIn(factura_id, results['conversion']['remitted'])
                self.assertNotIn(factura_id, results['conversion']['migrated'])
        else:
            self.assertEqual(invoice['payment_type'][0], self.card_type_id)
            self.assertFalse(invoice['payment_order_id'])
            self.assertTrue(results['conversion']['migrated'])
            if first_commits:
                self.assertIsInstance(errors.get('remittance'), osv.except_osv)
                self.assertIn('cobrament recurrent per targeta', errors['remittance'].value)
            else:
                self.assertEqual(errors, {})

    def _assert_eligibility_is_rechecked_after_waiting(self, values):
        factura_id, invoice_id, polissa_id, unused = self._prepare_invoice_and_order()
        selected = threading.Event()
        finished = threading.Event()
        results = []
        errors = []
        original_search = self.factura_obj.search
        self.invoice_obj.write(self.cursor, self.uid, [invoice_id], values)

        def search(cursor, uid, domain, *args, **kwargs):
            ids = original_search(cursor, uid, domain, *args, **kwargs)
            if not selected.is_set():
                selected.set()
            return ids

        def convert():
            cursor = self.database_obj.cursor()
            try:
                cursor.execute("SET LOCAL statement_timeout = '15s'")
                results.append(self.factura_obj.migrate_recurring_card_invoices(
                    cursor, self.uid, polissa_id, self.card_type_id,
                    date.today().strftime('%Y-%m-%d'), context={'lang': 'en_US'},
                ))
                cursor.commit()
            except Exception as error:
                cursor.rollback()
                errors.append(error)
            finally:
                cursor.close()
                finished.set()

        worker = threading.Thread(target=convert)
        with mock.patch.object(self.factura_obj, 'search', side_effect=search):
            try:
                worker.start()
                self.assertTrue(selected.wait(10))
                self.assertFalse(finished.wait(0.5))
            finally:
                self.cursor.commit()
                worker.join(20)

        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertIn(
            {'id': factura_id, 'reason_code': 'invoice_not_eligible'}, results[0]['unchanged']
        )
        self.assertNotIn(factura_id, results[0]['migrated'])
        invoice = self.invoice_obj.read(self.cursor, self.uid, invoice_id, ['payment_type'])
        self.assertFalse(invoice['payment_type'])

    def test_paid_while_waiting_is_not_converted(self):
        self._assert_eligibility_is_rechecked_after_waiting({'state': 'paid'})

    def test_due_date_changed_while_waiting_is_not_converted(self):
        self._assert_eligibility_is_rechecked_after_waiting({'date_due': '2000-01-01'})

    def test_remittance_first_prevents_card_conversion(self):
        self._assert_routes_are_serialized('remittance')

    def test_conversion_first_prevents_remittance(self):
        self._assert_routes_are_serialized('conversion')

    def test_remittance_rollback_allows_card_conversion(self):
        self._assert_routes_are_serialized('remittance', first_commits=False)

    def test_conversion_rollback_allows_remittance(self):
        self._assert_routes_are_serialized('conversion', first_commits=False)
