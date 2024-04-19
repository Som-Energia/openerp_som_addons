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
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_id = imd_obj.get_object_reference(
            cursor, uid,
            'giscedata_polissa', 'polissa_0002'
        )[1]
        pol = pol_obj.browse(cursor, uid, pol_id)
        cons_obj.write(cursor, uid, {'state': 'closed', 'date_closed': '2020-01-01 00:00:00'})

        self.assertTrue(pol.consulta_pobresa_pendent)

    def test_ff_consulta_pobresa_pendent_sense_consulta(self):
        cursor = self.cursor
        uid = self.uid
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_id = imd_obj.get_object_reference(
            cursor, uid,
            'giscedata_polissa', 'polissa_0001'
        )[1]
        pol = pol_obj.browse(cursor, uid, pol_id)

        self.assertTrue(pol.consulta_pobresa_pendent)
