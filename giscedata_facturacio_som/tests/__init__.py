# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
from tools.misc import cache


class TestGiscedataFacturacioSom(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.gff_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        super(TestGiscedataFacturacioSom, self).setUp()

    def set_account_invoice_number_cerca_exacte(self, cursor, uid, value):
        res_obj = self.openerp.pool.get('res.config')
        cache.clean_caches_for_db(cursor.dbname)
        res_obj.set(cursor, uid, 'account_invoice_number_cerca_exacte', value)

    def test_search_withPercentage_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, '1')

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [('number', 'ilike', '00%')])

        self.assertGreater(len(gff_ids), 1)

    def test_search_exactExist_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, '1')

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [('number', 'ilike', '0046/F')])

        self.assertEqual(len(gff_ids), 1)

    def test_search_exactNotExist_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, '1')

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [('number', 'ilike', '00')])

        self.assertEqual(len(gff_ids), 0)

    def test_search_withPercentage_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, '0')

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [('number', 'ilike', '00%')])

        self.assertGreater(len(gff_ids), 1)

    def test_search_exactExist_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, '0')

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [('number', 'ilike', '0046/F')])

        self.assertEqual(len(gff_ids), 1)

    def test_search_exactNotExist_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, '0')

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [('number', 'ilike', '00')])

        self.assertGreater(len(gff_ids), 1)
