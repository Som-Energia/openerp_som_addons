# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction

from ..invoice_pdf_storer import InvoicePdfStorer


class TestInvoicePdfStorer(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.conf_obj = self.openerp.pool.get("res.config")

    def tearDown(self):
        self.txn.stop()

    def test_is_enabled(self):
        self.conf_obj.set(self.cursor, self.uid, "factura_pdf_cache_flags", "")
        storer = InvoicePdfStorer(self.cursor, self.uid)
        self.assertFalse(storer.is_enabled())

        self.conf_obj.set(self.cursor, self.uid, "factura_pdf_cache_flags", "['Enabled']")
        storer = InvoicePdfStorer(self.cursor, self.uid)
        self.assertTrue(storer.is_enabled())

        storer = InvoicePdfStorer(self.cursor, self.uid, {"do_not_use_stored_pdf": True})
        self.assertFalse(storer.is_enabled())
