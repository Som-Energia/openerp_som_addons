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
        pol_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0002"
        )[1]
        context = {"active_ids": [pol_id], "active_id": pol_id}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        wiz_obj.crear_consulta_pobresa(cursor, uid, wiz_id, context=context)

        cons_list = cons_obj.search(cursor, uid, [('polissa_id', '=', pol_id)])
        self.assertEqual(len(cons_list), 1)
