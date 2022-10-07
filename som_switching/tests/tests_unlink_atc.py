# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
from osv.osv import except_osv
import mock
from .. import giscedata_switching
from .. import giscedata_atc

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

    def test__case_cancel_ATC_without_R1associat__cancelATC(self):
        """
        Test case_cancel for atc without R1 associat ATC is cancelled
        """

        atc_o = self.pool.get('giscedata.atc')
        imd_obj = self.openerp.pool.get('ir.model.data')

        atc_id = imd_obj.get_object_reference(self.cursor, self.uid, 'som_switching', 'cas_atc_0001')[1]
        atc_o.write(self.cursor, self.uid, atc_id, {'state': 'open'})

        atc_o.case_cancel(self.cursor, self.uid, atc_id)

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, 'cancel')

    def test__case_cancel_ATC_with_R101__NOCancelATC(self):
        """
        Test case_cancel for atc 'open' with R101 without enviament_pendent, ATC is NOT cancelled
        """
        atc_o = self.pool.get('giscedata.atc')
        imd_obj = self.openerp.pool.get('ir.model.data')

        atc_id = imd_obj.get_object_reference(self.cursor, self.uid, 'som_switching', 'cas_atc_0001')[1]

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        atc_o.write(self.cursor, self.uid, atc_id, {'state': 'open', 'ref': 'giscedata.switching,1'})

        try:
            atc_o.case_cancel(self.cursor, self.uid, atc_id)
        except Exception, e:
            atc_e = e

        self.assertEqual(atc_e.value, 'Cas ATC {} no es pot cancel·lar: R1 01 enviat a distribuïdora, per cancel·lar cal anul·lar amb un 08 i esperar el 09'.format(atc_id))

        atc = atc_o.browse(self.cursor, self.uid, atc_id)

        self.assertEqual(atc.state, 'open')