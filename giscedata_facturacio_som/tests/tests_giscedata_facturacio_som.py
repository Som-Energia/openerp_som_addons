# -*- coding: utf-8 -*-

from destral import testing
from tools.misc import cache


class TestGiscedataFacturacioSom(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.gff_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        super(TestGiscedataFacturacioSom, self).setUp()
        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("origin", "=", False)], limit=2)
        self.gff_obj.write(self.cursor, self.uid, gff_ids[0], {"origin": "sample_origin1"})
        self.gff_obj.write(self.cursor, self.uid, gff_ids[1], {"origin": "sample_origin2"})

    def set_account_invoice_number_cerca_exacte(self, cursor, uid, value):
        res_obj = self.openerp.pool.get("res.config")
        cache.clean_caches_for_db(cursor.dbname)
        res_obj.set(cursor, uid, "account_invoice_number_cerca_exacte", value)

    def test_search_withPercentage_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "1")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("number", "ilike", "00%")])

        self.assertGreater(len(gff_ids), 1)

    def test_search_exactExist_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "1")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("number", "ilike", "0046/F")])

        self.assertEqual(len(gff_ids), 1)

    def test_search_exactNotExist_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "1")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("number", "ilike", "00")])

        self.assertEqual(len(gff_ids), 0)

    def test_search_withPercentage_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "0")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("number", "ilike", "00%")])

        self.assertGreater(len(gff_ids), 1)

    def test_search_exactExist_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "0")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("number", "ilike", "0046/F")])

        self.assertEqual(len(gff_ids), 1)

    def test_search_exactNotExist_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "0")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("number", "ilike", "00")])

        self.assertGreater(len(gff_ids), 1)

    def set_invoice_origin_cerca_exacte(self, cursor, uid, value):
        res_obj = self.openerp.pool.get("res.config")
        cache.clean_caches_for_db(cursor.dbname)
        res_obj.set(cursor, uid, "invoice_origin_cerca_exacte", value)

    def test_search_withPercentage_active(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        gff_ids = self.gff_obj.search(
            self.cursor, self.uid, [("origin", "ilike", "sample_origin%")]
        )
        self.assertGreater(len(gff_ids), 1)

    def test_search_exactExist_active(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        gff_ids = self.gff_obj.search(
            self.cursor, self.uid, [("origin", "ilike", "sample_origin1")]
        )

        self.assertEqual(len(gff_ids), 1)

    def test_search_exactNotExist_active(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin")])

        self.assertEqual(len(gff_ids), 0)

    def test_search_withPercentage_disabled(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        gff_ids = self.gff_obj.search(
            self.cursor, self.uid, [("origin", "ilike", "sample_origin%")]
        )

        self.assertGreater(len(gff_ids), 1)

    def test_search_exactExist_disabled(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        gff_ids = self.gff_obj.search(
            self.cursor, self.uid, [("origin", "ilike", "sample_origin1")]
        )

        self.assertEqual(len(gff_ids), 1)

    def test_search_exactNotExist_disabled(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        gff_ids = self.gff_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin")])

        self.assertGreater(len(gff_ids), 1)
