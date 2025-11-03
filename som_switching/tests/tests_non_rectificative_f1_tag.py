# -*- coding: utf-8 -*-

from destral.transaction import Transaction
from giscedata_switching.tests.common_tests import TestSwitchingImport


class TestNonRectificativeF1Tag(TestSwitchingImport):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get("ir.model.data")
        self.f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        self.f1f_obj = self.pool.get("giscedata.facturacio.importacio.linia.factura")
        self.tarifa_obj = self.pool.get("giscedata.polissa.tarifa")
        self.prod_obj = self.pool.get("product.pricelist")

    def tearDown(self):
        self.txn.stop()

    def get_oref(self, module, name):
        return self.imd_obj.get_object_reference(
            self.cursor, self.uid, module, name
        )[1]

    def test__non_rectificative_f1R__not_F1_R(self):
        f1_id = self.get_oref("giscedata_facturacio_switching", "line_02_f1_import_01")
        f1n_ids = self.f1_obj._find_rectified_by_f1(self.cursor, self.uid, f1_id)
        self.assertEqual(f1n_ids, None)

    def test__non_rectificative_f1R__whithout_F1_R(self):
        f1N_id = self.get_oref("giscedata_facturacio_switching", "line_02_f1_import_01")
        f1R_id = self.get_oref("giscedata_facturacio_switching", "line_03_f1_import_01")
        f1N = self.f1_obj.browse(self.cursor, self.uid, f1N_id)
        txt = '12345N54321'
        self.f1_obj.write(
            self.cursor, self.uid, f1R_id,
            {
                'type_factura': 'R',
                'factura_rectificada': txt,
                'cups_id': f1N.cups_id.id,
            }
        )
        self.f1_obj.write(
            self.cursor, self.uid, f1N_id,
            {
                'invoice_number_text': txt + 'XYZ',
            }
        )

        found_id = self.f1_obj._find_rectified_by_f1(self.cursor, self.uid, f1R_id)
        self.assertEqual(found_id, None)

    def test__non_rectificative_f1R__F1_R(self):
        f1N_id = self.get_oref("giscedata_facturacio_switching", "line_02_f1_import_01")
        f1R_id = self.get_oref("giscedata_facturacio_switching", "line_03_f1_import_01")
        f1N = self.f1_obj.browse(self.cursor, self.uid, f1N_id)
        f1R = self.f1_obj.browse(self.cursor, self.uid, f1R_id)
        txt = '12345N54321'
        self.f1_obj.write(
            self.cursor, self.uid, f1R.id,
            {
                'type_factura': 'R',
                'factura_rectificada': txt,
                'cups_id': f1N.cups_id.id,
            }
        )
        self.f1_obj.write(
            self.cursor, self.uid, f1N.id,
            {
                'invoice_number_text': txt,
            }
        )

        found_id = self.f1_obj._find_rectified_by_f1(self.cursor, self.uid, f1R_id)
        self.assertEqual(found_id, f1N_id)

    def test__non_rectificative_f1R__not_equals_by_no_invoice_lines(self):
        f1N_id = self.get_oref("giscedata_facturacio_switching", "line_02_f1_import_01")
        f1R_id = self.get_oref("giscedata_facturacio_switching", "line_03_f1_import_01")
        f1N = self.f1_obj.browse(self.cursor, self.uid, f1N_id)
        f1R = self.f1_obj.browse(self.cursor, self.uid, f1R_id)
        txt = '12345N54321'
        self.f1_obj.write(
            self.cursor, self.uid, f1R.id,
            {
                'type_factura': 'R',
                'factura_rectificada': txt,
                'cups_id': f1N.cups_id.id,
            }
        )
        self.f1_obj.write(
            self.cursor, self.uid, f1N.id,
            {
                'invoice_number_text': txt,
            }
        )

        match = self.f1_obj._is_non_rectificative_f1R(self.cursor, self.uid, f1R_id, f1N_id)
        self.assertFalse(match)

    def test__non_rectificative_f1R__not_equals_by_no_invoice_line_in_N(self):
        f1N_id = self.get_oref("giscedata_facturacio_switching", "line_02_f1_import_01")
        f1R_id = self.get_oref("giscedata_facturacio_switching", "line_03_f1_import_01")
        f1N = self.f1_obj.browse(self.cursor, self.uid, f1N_id)
        f1R = self.f1_obj.browse(self.cursor, self.uid, f1R_id)
        txt = '12345N54321'
        self.f1_obj.write(
            self.cursor, self.uid, f1R.id,
            {
                'type_factura': 'R',
                'factura_rectificada': txt,
                'cups_id': f1N.cups_id.id,
            }
        )
        self.f1_obj.write(
            self.cursor, self.uid, f1N.id,
            {
                'invoice_number_text': txt,
            }
        )

        self.f1f_obj.create(
            self.cursor, self.uid,
            {
                'linia_id': f1R.id,
                'address_invoice_id': 1,
                'partner_id': 1,
                'account_id': 1,
                'polissa_id': 1,
                'tarifa_acces_id': 17,
                'cups_id': 1,
                'llista_preu': 11,
                'potencia': 1,
                'date_boe': '2022-01-01',
                'facturacio': 1,
            }
        )

        match = self.f1_obj._is_non_rectificative_f1R(self.cursor, self.uid, f1R_id, f1N_id)
        self.assertFalse(match)
