# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestWizardCrearConsultaPobresa(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test_wizard_crear_consulta_pobresa(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get("som.consulta.pobresa")
        wiz_obj = self.openerp.pool.get("wizard.crear.consulta.pobresa")
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')

        pol_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0001"
        )[1]
        fact_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0001'
        )[1]
        context = {"active_ids": [fact_id], "active_id": fact_id}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)

        result = wiz_obj.crear_consulta_pobresa(cursor, uid, wiz_id, context=context)

        cons_list = cons_obj.search(cursor, uid, [('polissa_id', '=', pol_id)])
        cons_data = cons_obj.browse(cursor, uid, cons_list[0])
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertTrue(str(cons_list) in result['domain'])
        self.assertEqual(cons_data.name, u'[0001C] Camptocamp (Alegr\xeda-Dulantzi)')
        self.assertEqual(cons_data.titular_id, u'Camptocamp')
        self.assertEqual(cons_data.direccio_cups, pol.cups.direccio)
        self.assertEqual(cons_data.email_partner, pol.direccio_notificacio.email)
