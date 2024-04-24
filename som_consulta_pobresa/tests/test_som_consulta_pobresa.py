# -*- coding: utf-8 -*-
from osv import osv
from destral import testing
from destral.transaction import Transaction


class TestConsultaPobresa(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_resolution_not_defined_when_close(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        cons_id = imd_obj.get_object_reference(
            cursor, uid,
            'som_consulta_pobresa', 'som_consulta_pobresa_demo_record'
        )[1]

        with self.assertRaises(osv.except_osv) as e:
            cons_obj.close_case(cursor, uid, [cons_id])

        self.assertEqual(
            e.exception.message,
            "warning -- Falta resoluci\xc3\xb3\n\nPer poder tancar la consulta s'ha d'informar el camp resolució."  # noqa: E501
        )

    def test_resolution_defined_when_close(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        cons_id = imd_obj.get_object_reference(
            cursor, uid,
            'som_consulta_pobresa', 'som_consulta_pobresa_demo_record'
        )[1]
        cons_obj.write(cursor, uid, cons_id, {'resolucio': 'positiva'})

        cons_obj.close_case(cursor, uid, [cons_id])

        state = cons_obj.read(cursor, uid, cons_id, ['state'])['state']
        self.assertEqual(state, 'done')

    def test_consulta_pobresa_activa_none(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001')[1]
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus')[1]

        result = cons_obj.consulta_pobresa_activa(cursor, uid, [], partner_id, polissa_id)

        self.assertFalse(result)

    def test_consulta_pobresa_activa_any(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        cons_id = imd_obj.get_object_reference(
            cursor, uid,
            'som_consulta_pobresa', 'som_consulta_pobresa_demo_record'
        )[1]
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0002')[1]
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus')[1]
        cons_obj.write(cursor, uid, cons_id, {'resolucio': 'positiva'})
        cons_obj.close_case(cursor, uid, [cons_id])

        result = cons_obj.consulta_pobresa_activa(cursor, uid, [], partner_id, polissa_id)

        self.assertTrue(result)
