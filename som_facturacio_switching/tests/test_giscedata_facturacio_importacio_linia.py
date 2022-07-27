# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
from tools.misc import cache
import mock
from mock import call
from datetime import datetime, timedelta

class TestGiscedataFacturacioImportacioLinia(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.f1_obj = self.openerp.pool.get('giscedata.facturacio.importacio.linia')
        self.imd_obj = self.openerp.pool.get('ir.model.data')
        super(TestGiscedataFacturacioImportacioLinia, self).setUp()
        f1_ids = self.f1_obj.search(self.cursor, self.uid, [('invoice_number_text', '=', False)], limit=2)
        self.f1_obj.write(self.cursor, self.uid, f1_ids[0], {'invoice_number_text': 'sample_origin1'})
        self.f1_obj.write(self.cursor, self.uid, f1_ids[1], {'invoice_number_text': 'sample_origin2'})

    def set_invoice_origin_cerca_exacte(self, cursor, uid, value):
        res_obj = self.openerp.pool.get('res.config')
        cache.clean_caches_for_db(cursor.dbname)
        res_obj.set(cursor, uid, 'invoice_origin_cerca_exacte', value)

    def test_search_withPercentage_active(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, '1')

        f1_ids = self.f1_obj.search(self.cursor, self.uid, [('invoice_number_text', 'ilike', 'sample_origin%')])
        self.assertGreater(len(f1_ids), 1)

    def test_search_exactExist_active(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, '1')

        f1_ids = self.f1_obj.search(self.cursor, self.uid, [('invoice_number_text', 'ilike', 'sample_origin1')])

        self.assertEqual(len(f1_ids), 1)

    def test_search_exactNotExist_active(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, '1')

        f1_ids = self.f1_obj.search(self.cursor, self.uid, [('invoice_number_text', 'ilike', 'sample_origin')])

        self.assertEqual(len(f1_ids), 0)

    def test_search_withPercentage_disabled(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, '0')

        f1_ids = self.f1_obj.search(self.cursor, self.uid, [('invoice_number_text', 'ilike', 'sample_origin%')])

        self.assertGreater(len(f1_ids), 1)

    def test_search_exactExist_disabled(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, '0')

        f1_ids = self.f1_obj.search(self.cursor, self.uid, [('invoice_number_text', 'ilike', 'sample_origin1')])

        self.assertEqual(len(f1_ids), 1)

    def test_search_exactNotExist_disabled(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, '0')

        f1_ids = self.f1_obj.search(self.cursor, self.uid, [('invoice_number_text', 'ilike', 'sample_origin')])

        self.assertGreater(len(f1_ids), 1)

    @mock.patch("som_facturacio_switching.giscedata_facturacio_importacio_linia.GiscedataFacturacioImportacioLinia.reimport_f1_by_cups")
    def test_do_reimport_f1_select_one_f1(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', 'line_01_f1_import_01'
        )[1]
                
        fecha_factura = (datetime.today() - timedelta(days=10)).strftime('%Y-%m-%d')
        self.f1_obj.write(self.cursor, self.uid, f1_id, {
            'info':"* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",
            'fecha_factura': fecha_factura
        })

        data = {'error_codes': [{'code': '2999', 'text': 'no file in gridfs'}], 'days_to_check': 30}
        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        mock_function.assert_called_with(self.cursor, self.uid, [f1_id], context={})


    @mock.patch("som_facturacio_switching.giscedata_facturacio_importacio_linia.GiscedataFacturacioImportacioLinia.reimport_f1_by_cups")
    def test_do_reimport_f1_no_select_older_f1(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', 'line_01_f1_import_01'
        )[1]
                
        fecha_factura = (datetime.today() - timedelta(days=40)).strftime('%Y-%m-%d')
        self.f1_obj.write(self.cursor, self.uid, f1_id, {
            'info':"* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",
            'fecha_factura': fecha_factura
        })

        data = {'error_codes': [{'code': '2999', 'text': 'no file in gridfs'}], 'days_to_check': 30}
        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        mock_function.assert_not_called()

    @mock.patch("giscedata_facturacio_switching.giscedata_facturacio_switching.GiscedataFacturacioImportacioLinia.process_line")
    def test_do_reimport_f1_two_f1_same_cups(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', 'line_01_f1_import_01'
        )[1]
        f2_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', 'line_02_f1_import_01'
        )[1]
        cups_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_cups', 'cups_04'
        )[1]
        fecha_factura = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        vals = {
            'info':"* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",
            'fecha_factura': fecha_factura, 
            'cups_id': cups_id
        }

        self.f1_obj.write(self.cursor, self.uid, [f1_id, f2_id], vals)
        self.f1_obj.write(self.cursor, self.uid, f1_id, {'fecha_factura_desde': '2022-02-02'})
        self.f1_obj.write(self.cursor, self.uid, f2_id, {'fecha_factura_desde': '2022-01-02'})
        data = {'error_codes': [{'code': '2999', 'text': 'no file in gridfs'}], 'days_to_check': 30}
        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        mock_function.assert_called_with(self.cursor, self.uid, [f2_id, f1_id], context={})

    @mock.patch("giscedata_facturacio_switching.giscedata_facturacio_switching.GiscedataFacturacioImportacioLinia.process_line")
    def test_do_reimport_f1_two_f1_different_cups(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', 'line_01_f1_import_01'
        )[1]
        f2_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', 'line_02_f1_import_01'
        )[1]
        cups1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_cups', 'cups_03'
        )[1]
        cups2_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_cups', 'cups_04'
        )[1]
        fecha_factura = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        vals = {
            'info':"* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",
            'fecha_factura': fecha_factura,
        }

        self.f1_obj.write(self.cursor, self.uid, [f1_id, f2_id], vals)
        self.f1_obj.write(self.cursor, self.uid, f1_id, {'fecha_factura_desde': '2022-01-02','cups_id': cups1_id})
        self.f1_obj.write(self.cursor, self.uid, f2_id, {'fecha_factura_desde': '2022-02-02','cups_id': cups2_id})
        data = {'error_codes': [{'code': '2999', 'text': 'no file in gridfs'}], 'days_to_check': 30}
        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        self.assertEqual(mock_function.call_count, 2)
        mock_function.assert_has_calls([call(self.cursor, self.uid, [f1_id], context={}), call(self.cursor, self.uid, [f2_id], context={})])
