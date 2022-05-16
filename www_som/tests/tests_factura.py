# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
from datetime import datetime
import json


def remove_ids(results):
    return remove_from(results, ['id', 'amount_total', 'enviat', 'visible'])

def remove_from(results, to_remove):
    for result in results:
        for item in to_remove:
            result.pop(item)
    return results


class TestFacturaWwwUltimesFactures(testing.OOTestCase):

    @classmethod
    def setUpClass(cls):
        """ To avoid calling it for each test
        """
        super(TestFacturaWwwUltimesFactures, cls).setUpClass()
        cls.openerp.install_module(
            'giscedata_tarifas_pagos_capacidad_20170101'
        )
        cls.openerp.install_module(
            'giscedata_tarifas_peajes_20170101'
        )
        cls.openerp.install_module(
            'som_account_invoice_pending'
        )

    def setUp(self):
        self.imd_obj = self.model('ir.model.data')
        self.par_obj = self.model('res.partner')
        self.pol_obj = self.model('giscedata.polissa')
        self.inv_obj = self.model('giscedata.facturacio.factura')
        self.i_obj = self.model('account.invoice')
        self.ips_obj = self.model('account.invoice.pending.state')
        self.msr_obj = self.model('giscedata.lectures.lectura')
        self.wz_mi_obj = self.model('wizard.manual.invoice')
        self.journal_obj = self.model('account.journal')
        self.am_obj = self.model('account.move')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    # Scenario contruction helpers
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        return self.imd_obj.get_object_reference(
            self.txn.cursor, self.txn.user,
            model,
            reference
        )[1]

    def get_contract_payer_vat_name(self, pol_id):
        cursor = self.txn.cursor
        uid = self.txn.user

        payer_id = self.pol_obj.read(
            cursor, uid,
            pol_id,
            ['pagador'])['pagador'][0]
        vat = self.par_obj.read(
            cursor, uid,
            payer_id,
            ['vat'])['vat']
        return vat

    def prepare_contract(self, pol_id, data_alta, data_ultima_lectura):
        cursor = self.txn.cursor
        uid = self.txn.user

        vals = {
            'data_alta': data_alta,
            'data_baixa': False,
            'data_ultima_lectura': data_ultima_lectura,
            'facturacio': 1,
            'facturacio_potencia': 'icp',
            'tg': '1',
            'lot_facturacio': False
        }
        self.pol_obj.write(cursor, uid, pol_id, vals)
        self.pol_obj.send_signal(cursor, uid, [pol_id], [
            'validar', 'contracte'
        ])
        contract = self.pol_obj.browse(cursor, uid, pol_id)
        for meter in contract.comptadors:
            for l in meter.lectures:
                l.unlink(context={})
            for lp in meter.lectures_pot:
                lp.unlink(context={})
            meter.write({'lloguer': False})
        return contract.comptadors[0].id

    def create_measure(self, meter_id, date_measure, measure):
        periode_id = self.get_fixture('giscedata_polissa', 'p1_e_tarifa_20A_new')
        origen_id = self.get_fixture('giscedata_lectures', 'origen10')

        vals = {
            'name': date_measure,
            'periode': periode_id,
            'lectura': measure,
            'tipus': 'A',
            'comptador': meter_id,
            'observacions': '',
            'origen_id': origen_id,
        }
        return self.msr_obj.create(self.txn.cursor, self.txn.user, vals)

    def create_invoice(self, pol_id, meter_id, date_start, date_end, name, context=None):
        cursor = self.txn.cursor
        uid = self.txn.user

        journal_id = self.journal_obj.search(
            cursor, uid,
            [('code', '=', 'ENERGIA')]
        )[0]
        wz_fact_id = self.wz_mi_obj.create(cursor, uid, {})
        wz_fact = self.wz_mi_obj.browse(cursor, uid, wz_fact_id)
        wz_fact.write({
            'polissa_id': pol_id,
            'date_start': date_start,
            'date_end': date_end,
            'journal_id': journal_id
        })
        wz_fact.action_manual_invoice()
        wz_fact = self.wz_mi_obj.browse(cursor, uid, wz_fact_id)
        inv_id = json.loads(wz_fact.invoice_ids)[0]

        if not context:
            context = {}
        context['number'] = name
        self.inv_obj.write(cursor, uid, inv_id, context)

        return inv_id

    def create_invoice_related(self, pol_id, meter_id, fact_id, context):
        cursor = self.txn.cursor
        uid = self.txn.user

        fact_vals = self.inv_obj.read(
            cursor, uid,
            fact_id,
            ['data_inici', 'data_final', 'number']
            )

        head = context.pop('number_head')
        return self.create_invoice(
            pol_id,
            meter_id,
            fact_vals['data_inici'],
            fact_vals['data_final'],
            head + fact_vals['number'],
            context)

    def create_invoice_ab(self, pol_id, meter_id, fact_id, context):
        if not context:
            context = {}
        context['tipo_rectificadora'] = 'B'
        context['type'] = 'out_refund'
        context['ref'] = fact_id
        context['number_head'] = 'AB-'

        return self.create_invoice_related(pol_id, meter_id, fact_id, context)

    def create_invoice_re(self, pol_id, meter_id, fact_id, context=None):
        if not context:
            context = {}
        context['tipo_rectificadora'] = 'R'
        context['type'] = 'out_invoice'
        context['ref'] = fact_id
        context['number_head'] = 'RE-'

        return self.create_invoice_related(pol_id, meter_id, fact_id, context)

    def create_pending_state(self, fact_id, name, weight=10, process_id=1):
        ips_id = self.ips_obj.create(
            self.cursor,
            self.uid,
            {
                'process_id': process_id,
                'name': name,
                'weight': weight,
            })
        self.set_pending_state(fact_id, ips_id)
        return ips_id

    def set_pending_state(self, fact_id, pending_state_id):
        inv_id = self.inv_obj.read(
            self.cursor,
            self.uid,
            fact_id,
            ['invoice_id'])['invoice_id'][0]
        self.i_obj.set_pending(
            self.cursor,
            self.uid,
            inv_id,
            pending_state_id)

    def create_dummy_group_move(self, inv_id):
        am_id = self.am_obj.create(
            self.cursor,
            self.uid,
            {
                'name': 'dummy',
                'journal_id': 1,
            })
        self.inv_obj.write(
            self.cursor,
            self.uid,
            inv_id,
            {'group_move_id': am_id})

    # ------------------------------------------------------
    # Main cases testing functions for www_ultimes_factures
    # ------------------------------------------------------
    def test_www_ultimes_factures__bad_vat_nok(self):
        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            'Not_a_VAT'))
        self.assertEqual([], results)

    def test_www_ultimes_factures__unknown_vat_nok(self):
        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            '12345678Z'))
        self.assertEqual([], results)

    def test_www_ultimes_factures__vat_ok_empty(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))
        self.assertEqual([], results)

    def test_www_ultimes_factures__1ok_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__2ok_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__2ok_1draft_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-04-10', '2017-05-10', 'FE0003', {'state': 'draft'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__3ok_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'paid'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[2], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__3ok_and_1ab_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})
        inv3_id = self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'paid'})
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {'state': 'paid'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 4)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'AB-FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ABONADORA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[2], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[3], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__3ok_and_1ab_1re_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})
        inv3_id = self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'paid'})
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {'state': 'paid'})
        self.create_invoice_re(pol_id, meter_id, inv3_id, {'state': 'paid'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 5)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'RE-FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'RECTIFICADORA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'AB-FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ABONADORA',
            })
        self.assertEqual(results[2], {
            'polissa_id': 1,
            'number': u'FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[3], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[4], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__3ok_and_1ab_1re_2_not_visible_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})
        inv3_id = self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'paid', 'visible_ov': False})
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {'state': 'paid', 'visible_ov': False})
        self.create_invoice_re(pol_id, meter_id, inv3_id, {'state': 'paid'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 5)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'RE-FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'RECTIFICADORA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'AB-FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ABONADORA',
            })
        self.assertEqual(results[2], {
            'polissa_id': 1,
            'number': u'FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[3], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[4], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__3ok_sent_not_paid_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'open'})
        self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'open'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'EN_PROCES',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'EN_PROCES',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[2], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'EN_PROCES',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__3ok_last_sent_not_paid_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'open'})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'EN_PROCES',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[2], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__3ok_last_sent_not_paid_invisible_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'open'})
        self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'open', 'visible_ov': False})

        results = remove_ids(self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], {
            'polissa_id': 1,
            'number': u'FE0003',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-04-18',
            'data_final': '2017-05-17',
            'estat_pagament': 'EN_PROCES',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[1], {
            'polissa_id': 1,
            'number': u'FE0002',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-03-18',
            'data_final': '2017-04-17',
            'estat_pagament': 'EN_PROCES',
            'tipus': 'ORDINARIA',
            })
        self.assertEqual(results[2], {
            'polissa_id': 1,
            'number': u'FE0001',
            'date_invoice': datetime.today().strftime('%Y-%m-%d'),
            'data_inici': '2017-02-18',
            'data_final': '2017-03-17',
            'estat_pagament': 'PAGADA',
            'tipus': 'ORDINARIA',
            })

    def test_www_ultimes_factures__AB_negatives_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        self.create_measure(meter_id, '2017-04-15', 9000)
        self.create_measure(meter_id, '2017-05-15', 9350)
        inv1_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        inv2_id = self.create_invoice(pol_id, meter_id, '2017-03-18', '2017-04-17', 'FE0002', {'state': 'paid'})
        inv3_id = self.create_invoice(pol_id, meter_id, '2017-04-18', '2017-05-17', 'FE0003', {'state': 'paid'})
        self.create_invoice_ab(pol_id, meter_id, inv1_id, {'state': 'paid'})
        self.create_invoice_ab(pol_id, meter_id, inv2_id, {'state': 'paid'})
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {'state': 'paid'})
        self.create_invoice_re(pol_id, meter_id, inv1_id, {'state': 'paid'})
        self.create_invoice_re(pol_id, meter_id, inv2_id, {'state': 'paid'})
        self.create_invoice_re(pol_id, meter_id, inv3_id, {'state': 'paid'})

        results = self.inv_obj.www_ultimes_factures(
            self.cursor,
            self.uid,
            vat_name)

        self.assertEqual(len(results), 9)

        self.assertEqual(results[0]['tipus'], 'RECTIFICADORA')
        self.assertGreater(results[0]['amount_total'], 0)
        self.assertEqual(results[1]['tipus'], 'RECTIFICADORA')
        self.assertGreater(results[1]['amount_total'], 0)
        self.assertEqual(results[2]['tipus'], 'RECTIFICADORA')
        self.assertGreater(results[2]['amount_total'], 0)

        self.assertEqual(results[3]['tipus'], 'ABONADORA')
        self.assertLess(results[3]['amount_total'], 0)
        self.assertEqual(results[4]['tipus'], 'ABONADORA')
        self.assertLess(results[4]['amount_total'], 0)
        self.assertEqual(results[5]['tipus'], 'ABONADORA')
        self.assertLess(results[5]['amount_total'], 0)

        self.assertEqual(results[6]['tipus'], 'ORDINARIA')
        self.assertGreater(results[6]['amount_total'], 0)
        self.assertEqual(results[7]['tipus'], 'ORDINARIA')
        self.assertGreater(results[7]['amount_total'], 0)
        self.assertEqual(results[8]['tipus'], 'ORDINARIA')
        self.assertGreater(results[8]['amount_total'], 0)

    # ----------------------------------------------------
    # Main cases testing functions for www_estat_pagament
    # ----------------------------------------------------
    def test_www_estat_pagament_ov__cancel_ERROR(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'cancel'})
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'ERROR')

    def test_www_estat_pagament_ov__draft_ERROR(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'draft'})
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'ERROR')

    def test_www_estat_pagament_ov__open_correct_EN_PROCES(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__open_reclama_EN_PROCES(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'R1 RECLAMACIÓ')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__open_1f_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'1F DEVOLUCIÓ')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_2f_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'2F DEVOL NO RESPOSTA')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_3f_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'3F DEVOL ÚLTIM AVÍS')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_4f_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'4F DUES FACTURES')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_6f_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'6F TALL')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_7f_ADV_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'7F ADVOCATS')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_7f_CUR_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'7F CUR')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_deli_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'DELICAT')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_no_rec_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'NO RECLAMEU')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_pact_g_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'PACTE GIRAR')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_pact_t_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'PACTE TRANSFER')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_pob_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'POBRESA')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__open_res_NO_PAGADA(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'open'})
        self.create_pending_state(inv_id, u'RESIDU')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'NO_PAGADA')

    def test_www_estat_pagament_ov__paid_correct_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.set_pending_state(inv_id, 1)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')

    def test_www_estat_pagament_ov__paid_no_reclama_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'NO RECLAMEU')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')

    def test_www_estat_pagament_ov__paid_no_pending_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')

    def test_www_estat_pagament_ov__paid_1F_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'1F DEVOLUCIÓ')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_3f_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'3F DEVOL ÚLTIM AVÍS')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_6f_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'6F TALL')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_7f_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'7F ADVOCATS')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_7f_cur_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'7F CUR')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_pacte_f_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'PACTE FRACCIO')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_pacte_t_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'PACTE TRANSFER')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_pob_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'POBRESA')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')

    def test_www_estat_pagament_ov__paid_rec_group_move(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id = self.prepare_contract(pol_id, '2017-01-01', '2017-02-15')
        self.create_measure(meter_id, '2017-02-15', 8000)
        self.create_measure(meter_id, '2017-03-15', 8600)
        inv_id = self.create_invoice(pol_id, meter_id, '2017-02-18', '2017-03-17', 'FE0001', {'state': 'paid'})
        self.create_pending_state(inv_id, u'R1 RECLAMACIÓ')
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'PAGADA')
        self.create_dummy_group_move(inv_id)
        payment_state = self.inv_obj.www_estat_pagament_ov(self.cursor, self.uid, inv_id)
        self.assertEqual(payment_state, 'EN_PROCES')
