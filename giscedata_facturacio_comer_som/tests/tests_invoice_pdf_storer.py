# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction

from ..invoice_pdf_storer import InvoicePdfStorer


_BLANK_PDF = """
%PDF-1.1
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000010 00000 n
0000000054 00000 n
0000000103 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
165
%%EOF
"""


class TestInvoicePdfStorer(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.conf_obj = self.openerp.pool.get("res.config")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")

    def tearDown(self):
        self.txn.stop()

    def test_is_enabled(self):
        self.conf_obj.set(self.cursor, self.uid, "factura_pdf_cache_flags", "")
        storer = InvoicePdfStorer(self.cursor, self.uid)
        self.assertFalse(storer.is_enabled())

        self.conf_obj.set(self.cursor, self.uid, "factura_pdf_cache_flags", "['Enabled']")
        storer = InvoicePdfStorer(self.cursor, self.uid)
        self.assertTrue(storer.is_enabled())

        storer = InvoicePdfStorer(self.cursor, self.uid, {"force_store_pdf_disabled": True})
        self.assertFalse(storer.is_enabled())

    def test_get_storable_fact_number(self):
        storer = InvoicePdfStorer(self.cursor, self.uid)

        # Draft invoice without number
        fact_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001")[1]
        self.assertFalse(storer.get_storable_fact_number(fact_id))

        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        self.assertFalse(storer.get_storable_fact_number(fact_id))

        self.fact_obj.write(self.cursor, self.uid, fact_id, {"number": "FE123"})
        self.assertEqual(storer.get_storable_fact_number(fact_id), "FE123")

    def test_get_store_filename(self):
        storer = InvoicePdfStorer(self.cursor, self.uid)
        self.assertEqual(storer.get_store_filename("FE123"), "STORED_FE123.pdf")

    def test_store_file(self):
        storer = InvoicePdfStorer(self.cursor, self.uid)

        fact_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001")[1]

        # Asserts than some attachment ID is returned (non 0 integers eval to True)
        self.assertTrue(storer.store_file(_BLANK_PDF, "STORED_FE123.pdf", fact_id))

        self.conf_obj.set(self.cursor, self.uid, "factura_pdf_cache_flags", "['Dont_store']")
        storer = InvoicePdfStorer(self.cursor, self.uid)
        self.assertFalse(storer.store_file(_BLANK_PDF, "STORED_FE123.pdf", fact_id))

    def test_read_file(self):
        storer = InvoicePdfStorer(self.cursor, self.uid)

        fact_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001")[1]

        att_id = storer.store_file(_BLANK_PDF, "STORED_FE123.pdf", fact_id)
        content, filetype = storer.read_file(att_id)

        self.assertEqual(filetype, "pdf")
        self.assertEqual(content, _BLANK_PDF)

    def test_search_and_retrieve_use_case(self):
        storer = InvoicePdfStorer(self.cursor, self.uid)

        fact_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001")[1]
        self.fact_obj.write(
            self.cursor, self.uid, fact_id, {"state": "open", "number": "FE123"})

        storer.store_file(_BLANK_PDF, "STORED_FE123.pdf", fact_id)

        storer.search_stored_and_append(fact_id)
        content, filetype = storer.retrieve()

        self.assertEqual(filetype, "pdf")
        self.assertEqual(content, _BLANK_PDF)

    def test_store_and_retrieve_use_case(self):
        storer = InvoicePdfStorer(
            self.cursor, self.uid, {"save_pdf_in_invoice_attachments": True})

        fact_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001")[1]
        self.fact_obj.write(
            self.cursor, self.uid, fact_id, {"state": "open", "number": "FE123"})

        storer.append_and_store(fact_id, (_BLANK_PDF, 'pdf'))

        content, filetype = storer.retrieve()

        self.assertEqual(filetype, "pdf")
        self.assertEqual(content, _BLANK_PDF)

    def test_multiple_pdf_use_case(self):
        storer = InvoicePdfStorer(
            self.cursor, self.uid, {"save_pdf_in_invoice_attachments": True})

        fact_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001")[1]
        self.fact_obj.write(
            self.cursor, self.uid, fact_id, {"state": "open", "number": "FE123"})

        storer.append_and_store(fact_id, (_BLANK_PDF, 'pdf'))

        # Here we find the last stored PDF and we append it in the result again
        storer.search_stored_and_append(fact_id)

        content, filetype = storer.retrieve()
        self.assertEqual(filetype, "pdf")

        # We check thant the content is larger than the original PDF (there are two pages now)
        self.assertGreater(len(content), len(_BLANK_PDF))
