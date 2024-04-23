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
            cursor, uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        process_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'bono_social_pending_state_process'
        )[1]
        pol_obj.write(cursor, uid, pol_id, {'state': 'activa', 'process_id': process_id})
        consulta_state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pendent_consulta_probresa_pending_state',
        )[1]
        fact_id = imd_obj.get_object_reference(
            cursor, uid, 'som_consulta_pobresa', 'factura_conceptes_0001',
        )[1]
        consulta_id = imd_obj.get_object_reference(
            cursor, uid, 'som_consulta_pobresa', 'som_consulta_pobresa_demo_record',
        )[1]
        cons_obj.write(cursor, uid, consulta_id, {
                       'state': 'done', 'date_closed': '2020-01-01 00:00:00'})
        fact = gff_obj.browse(cursor, uid, fact_id)
        fact.write({
            'state': 'open',
            'type': 'out_invoice'
        })
        fact.set_pending(consulta_state_id)

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
        process_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'bono_social_pending_state_process'
        )[1]
        pol_obj.write(cursor, uid, pol_id, {'state': 'activa', 'process_id': process_id})
        consulta_state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pendent_consulta_probresa_pending_state',
        )[1]
        fact_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0002',
        )[1]
        fact = gff_obj.browse(cursor, uid, fact_id)
        fact.write({
            'state': 'open',
            'type': 'out_invoice'
        })

        fact.set_pending(consulta_state_id)

        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertTrue(pol.consulta_pobresa_pendent)
