# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction

class TestUnlinkATC(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test__unlink_one_ATC__cancelATC(self):
        """
        Test per comprovar que l'unlink no elimina i cancela el cas
        """

        atc_o = self.pool.get('giscedata.atc')
        imd_obj = self.openerp.pool.get('ir.model.data')

        atc_id = imd_obj.get_object_reference(self.cursor, self.uid, 'som_switching', 'cas_atc_0001')[1]
        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc.unlink()

        self.assertEqual(atc.state, 'cancel')