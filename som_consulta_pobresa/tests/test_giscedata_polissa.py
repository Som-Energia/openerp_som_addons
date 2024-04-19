# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestGiscedataPolissa(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_ff_consulta_pobresa_pendent_vigent(self):
        cursor = self.cursor
        uid = self.uid
        self.openerp.pool.get('som.consulta.pobresa')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_id = imd_obj.get_object_reference(
            cursor, uid,
            'giscedata_polissa', 'polissa_0002'
        )[1]
        pol = pol_obj.browse(cursor, uid, pol_id)

        self.assertFalse(pol.consulta_pobresa_pendent)

    def test_ff_consulta_pobresa_pendent_novigent(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        gff_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_id = imd_obj.get_object_reference(
            cursor, uid,
            'giscedata_polissa', 'polissa_0002'
        )[1]
        consulta_state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pendent_consulta_probresa_pending_state',
        )
        fact_id = imd_obj.get_object_reference(
            cursor, uid, 'som_consulta_pobresa', 'factura_conceptes_0001',
        )
        fact = gff_obj.browse(cursor, uid, fact_id)
        fact.write(cursor, uid, {
            'state': 'open',
            'type': 'out_invoice'
        })
        fact.set_pending(consulta_state_id)
        cons_obj.write(cursor, uid, {'state': 'closed', 'date_closed': '2020-01-01 00:00:00'})

        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertTrue(pol.consulta_pobresa_pendent)

    def test_ff_consulta_pobresa_pendent_sense_consulta(self):
        cursor = self.cursor
        uid = self.uid
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        gff_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        pol_id = imd_obj.get_object_reference(
            cursor, uid,
            'giscedata_polissa', 'polissa_0001'
        )[1]
        consulta_state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pendent_consulta_probresa_pending_state',
        )
        fact_id = imd_obj.get_object_reference(
            cursor, uid, 'som_consulta_pobresa', 'factura_conceptes_0001',
        )
        fact = gff_obj.browse(cursor, uid, fact_id)
        fact.write(cursor, uid, {
            'state': 'open',
            'type': 'out_invoice'
        })
        fact.set_pending(consulta_state_id)

        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertTrue(pol.consulta_pobresa_pendent)
