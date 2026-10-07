# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from tools.misc import cache
import mock
from mock import call
from datetime import datetime, timedelta


class TestGiscedataFacturacioImportacioLinia(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.f1_obj = self.openerp.pool.get("giscedata.facturacio.importacio.linia")
        self.cups_obj = self.openerp.pool.get("giscedata.cups.ps")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        super(TestGiscedataFacturacioImportacioLinia, self).setUp()
        f1_ids = self.f1_obj.search(
            self.cursor, self.uid, [("invoice_number_text", "=", False)], limit=2
        )
        self.f1_obj.write(
            self.cursor, self.uid, f1_ids[0], {"invoice_number_text": "sample_origin1"}
        )
        self.f1_obj.write(
            self.cursor, self.uid, f1_ids[1], {"invoice_number_text": "sample_origin2"}
        )

    def set_invoice_origin_cerca_exacte(self, cursor, uid, value):
        res_obj = self.openerp.pool.get("res.config")
        cache.clean_caches_for_db(cursor.dbname)
        res_obj.set(cursor, uid, "invoice_origin_cerca_exacte", value)

    def test_search_withPercentage_active(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        f1_ids = self.f1_obj.search(
            self.cursor, self.uid, [("invoice_number_text", "ilike", "sample_origin%")]
        )
        self.assertGreater(len(f1_ids), 1)

    def test_search_exactExist_active(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        f1_ids = self.f1_obj.search(
            self.cursor, self.uid, [("invoice_number_text", "ilike", "sample_origin1")]
        )

        self.assertEqual(len(f1_ids), 1)

    def test_search_exactNotExist_active(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        f1_ids = self.f1_obj.search(
            self.cursor, self.uid, [("invoice_number_text", "ilike", "sample_origin")]
        )

        self.assertEqual(len(f1_ids), 0)

    def test_search_withPercentage_disabled(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        f1_ids = self.f1_obj.search(
            self.cursor, self.uid, [("invoice_number_text", "ilike", "sample_origin%")]
        )

        self.assertGreater(len(f1_ids), 1)

    def test_search_exactExist_disabled(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        f1_ids = self.f1_obj.search(
            self.cursor, self.uid, [("invoice_number_text", "ilike", "sample_origin1")]
        )

        self.assertEqual(len(f1_ids), 1)

    def test_search_exactNotExist_disabled(self):
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        f1_ids = self.f1_obj.search(
            self.cursor, self.uid, [("invoice_number_text", "ilike", "sample_origin")]
        )

        self.assertGreater(len(f1_ids), 1)

    @mock.patch(
        "som_facturacio_switching.giscedata_facturacio_importacio_linia.GiscedataFacturacioImportacioLinia.reimport_f1_by_cups"  # noqa: E501
    )
    def test_do_reimport_f1_select_one_f1(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]

        data_carrega = (datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        self.f1_obj.write(
            self.cursor,
            self.uid,
            f1_id,
            {
                "info": "* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",  # noqa: E501
                "data_carrega": data_carrega,
            },
        )

        data = {"error_codes": [{"code": "2999", "text": "no file in gridfs"}], "days_to_check": 30}
        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        mock_function.assert_called_with(self.cursor, self.uid, [f1_id], context={})

    @mock.patch(
        "som_facturacio_switching.giscedata_facturacio_importacio_linia.GiscedataFacturacioImportacioLinia.reimport_f1_by_cups"  # noqa: E501
    )
    def test_do_reimport_f1_no_select_older_f1(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        test_date = (datetime.today() - timedelta(days=40)).strftime("%Y-%m-%d")
        self.f1_obj.write(
            self.cursor, self.uid, f1_id,
            {
                "info": "* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",  # noqa: E501
                "data_carrega": test_date,
            },
        )
        data = {"error_codes": [{"code": "2999", "text": "no file in gridfs"}], "days_to_check": 30}

        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        mock_function.assert_not_called()

    @mock.patch(
        "giscedata_facturacio_switching.giscedata_facturacio_switching.GiscedataFacturacioImportacioLinia.process_line"  # noqa: E501
    )
    def test_do_reimport_f1_two_f1_same_cups(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        f2_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_02_f1_import_01"
        )[1]
        cups_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_04"
        )[1]
        cups_text = self.cups_obj.read(self.cursor, self.uid, cups_id, ['name'])['name']
        data_carrega = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        vals = {
            "info": "* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",  # noqa: E501
            "data_carrega": data_carrega,
            "cups_text": cups_text,
        }
        self.f1_obj.write(self.cursor, self.uid, [f1_id, f2_id], vals)
        self.f1_obj.write(self.cursor, self.uid, f1_id, {"fecha_factura_desde": "2022-02-02"})
        self.f1_obj.write(self.cursor, self.uid, f2_id, {"fecha_factura_desde": "2022-01-02"})
        data = {"error_codes": [{"code": "2999", "text": "no file in gridfs"}], "days_to_check": 30}

        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        mock_function.assert_has_calls(
            [
                call(self.cursor, self.uid, f1_id, context={}),
                call(self.cursor, self.uid, f2_id, context={}),
            ]
        )

    @mock.patch(
        "giscedata_facturacio_switching.giscedata_facturacio_switching.GiscedataFacturacioImportacioLinia.process_line"  # noqa: E501
    )
    def test_do_reimport_f1_two_f1_different_cups(self, mock_function):
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        f2_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_02_f1_import_01"
        )[1]
        cups1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_03"
        )[1]
        cups2_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_04"
        )[1]
        data_carrega = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        vals = {
            "info": "* [2999] Undefined error: no file in gridfs collection Collection(Database(MongoClient('', ), u''), u'fs') with _id ObjectId('5')",  # noqa: E501
            "data_carrega": data_carrega,
        }
        cups_text_1 = self.cups_obj.read(self.cursor, self.uid, cups1_id, ['name'])['name']
        cups_text_2 = self.cups_obj.read(self.cursor, self.uid, cups2_id, ['name'])['name']
        self.f1_obj.write(self.cursor, self.uid, [f1_id, f2_id], vals)
        self.f1_obj.write(
            self.cursor, self.uid, f1_id, {
                "fecha_factura_desde": "2022-01-02", "cups_text": cups_text_1}
        )
        self.f1_obj.write(
            self.cursor, self.uid, f2_id, {
                "fecha_factura_desde": "2022-02-02", "cups_text": cups_text_2}
        )
        data = {"error_codes": [{"code": "2999", "text": "no file in gridfs"}], "days_to_check": 30}
        self.f1_obj.do_reimport_f1(self.cursor, self.uid, data=data, context=None)

        self.assertEqual(mock_function.call_count, 2)
        mock_function.assert_has_calls(
            [
                call(self.cursor, self.uid, f2_id, context={}),
                call(self.cursor, self.uid, f1_id, context={}),
            ]
        )


class TestBatchF1Polissa(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestBatchF1Polissa, self).setUp()
        self.f1_obj = self.openerp.pool.get("giscedata.facturacio.importacio.linia")
        self.cups_obj = self.openerp.pool.get("giscedata.cups.ps")
        imd_obj = self.openerp.pool.get("ir.model.data")
        self.cups_ids = [
            imd_obj.get_object_reference(self.cursor, self.uid, "giscedata_cups", name)[1]
            for name in ("cups_03", "cups_04")
        ]
        self.polissa_ids = [
            imd_obj.get_object_reference(self.cursor, self.uid, "giscedata_polissa", name)[1]
            for name in ("polissa_0001", "polissa_0002", "polissa_0003", "polissa_0004")
        ]
        # Isolate the contract history used by the SQL lookup, without firing
        # unrelated stored-field recomputations. Destral rolls back these fixtures.
        self.cursor.execute(
            "UPDATE giscedata_polissa SET data_alta = NULL WHERE cups IN %s",
            (tuple(self.cups_ids),),
        )
        for polissa_id, cups_id, date, active, state in (
            (self.polissa_ids[0], self.cups_ids[0], "2024-01-01", True, "activa"),
            (self.polissa_ids[1], self.cups_ids[0], "2024-02-01", False, "baixa"),
            (self.polissa_ids[2], self.cups_ids[0], "2024-03-01", True, "esborrany"),
            (self.polissa_ids[3], self.cups_ids[1], "2024-01-15", True, "activa"),
        ):
            self.cursor.execute(
                "UPDATE giscedata_polissa SET cups = %s, data_alta = %s, "
                "active = %s, state = %s WHERE id = %s",
                (cups_id, date, active, state, polissa_id),
            )

    def invoice(self, f1_id, cups_id, date):
        return {"id": f1_id, "cups_id": (cups_id, "CUPS") if cups_id else False,
                "fecha_factura_desde": date}

    def resolve(self, invoices):
        with mock.patch.object(self.f1_obj, "read", return_value=invoices):
            return self.f1_obj._ff_get_polissa(
                self.cursor, self.uid, [invoice["id"] for invoice in invoices],
                "polissa_id", None, {},
            )

    def test_matches_previous_lookup_for_multiple_cups_and_dates(self):
        invoices = [
            self.invoice(1, self.cups_ids[0], "2023-12-30"),
            self.invoice(2, self.cups_ids[0], "2023-12-31"),
            self.invoice(3, self.cups_ids[0], "2024-01-30"),
            self.invoice(4, self.cups_ids[0], "2024-01-31"),
            self.invoice(5, self.cups_ids[0], "2024-02-29"),
            self.invoice(6, self.cups_ids[1], "2024-01-13"),
            self.invoice(7, self.cups_ids[1], "2024-01-14"),
            self.invoice(8, self.cups_ids[1], "2024-03-01"),
        ]
        expected = {}
        for invoice in invoices:
            cups_id = invoice["cups_id"][0]
            date = (datetime.strptime(invoice["fecha_factura_desde"], "%Y-%m-%d")
                    + timedelta(days=1)).strftime("%Y-%m-%d")
            expected[invoice["id"]] = self.cups_obj.find_most_recent_polissa(
                self.cursor, self.uid, cups_id, date
            )[cups_id]
        self.assertEqual(self.resolve(invoices), expected)
        self.assertEqual(expected[4], self.polissa_ids[1])
        self.assertEqual(expected[5], self.polissa_ids[2])
        self.assertFalse(expected[1])

    def test_missing_cups_or_date_does_not_query_contracts(self):
        invoices = [self.invoice(1, False, "2024-01-01"),
                    self.invoice(2, self.cups_ids[0], False)]
        with mock.patch.object(self.cursor, "execute", wraps=self.cursor.execute) as execute:
            self.assertEqual(self.resolve(invoices), {1: False, 2: False})
        execute.assert_not_called()

    def test_empty_batch_does_not_read_or_query(self):
        with mock.patch.object(self.f1_obj, "read") as read:
            self.assertEqual(self.f1_obj._ff_get_polissa(
                self.cursor, self.uid, [], "polissa_id", None, {}
            ), {})
        read.assert_not_called()

    def test_large_batch_uses_one_contract_query(self):
        invoices = [
            self.invoice(f1_id, self.cups_ids[f1_id % 2], "2024-01-31")
            for f1_id in range(1, 313)
        ]
        with mock.patch.object(self.cursor, "execute", wraps=self.cursor.execute) as execute:
            result = self.resolve(invoices)
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(len(result), 312)
        for invoice in invoices:
            expected = self.polissa_ids[1] if invoice["cups_id"][0] == self.cups_ids[0] else (
                self.polissa_ids[3]
            )
            self.assertEqual(result[invoice["id"]], expected)

    def test_changes_to_contract_dates_are_not_cached_between_calls(self):
        invoices = [self.invoice(1, self.cups_ids[0], "2024-01-31")]
        self.assertEqual(self.resolve(invoices), {1: self.polissa_ids[1]})
        self.cursor.execute(
            "UPDATE giscedata_polissa SET data_alta = '2024-02-02' WHERE id = %s",
            (self.polissa_ids[1],),
        )
        self.assertEqual(self.resolve(invoices), {1: self.polissa_ids[0]})

    def test_cups_without_dated_contract_returns_false(self):
        self.cursor.execute(
            "UPDATE giscedata_polissa SET data_alta = NULL WHERE cups = %s",
            (self.cups_ids[1],),
        )
        self.assertEqual(self.resolve([
            self.invoice(1, self.cups_ids[1], "2024-01-31")
        ]), {1: False})

    def test_equal_activation_dates_return_an_eligible_contract(self):
        self.cursor.execute(
            "UPDATE giscedata_polissa SET data_alta = '2024-02-01' WHERE id = %s",
            (self.polissa_ids[2],),
        )
        result = self.resolve([self.invoice(1, self.cups_ids[0], "2024-01-31")])
        self.assertIn(result[1], self.polissa_ids[1:3])

    def test_stored_field_is_recomputed_after_invoice_date_changes(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        cups_text = self.cups_obj.read(
            self.cursor, self.uid, self.cups_ids[0], ["name"]
        )["name"]
        self.f1_obj.write(self.cursor, self.uid, f1_id, {
            "cups_text": cups_text, "cups_id": self.cups_ids[0],
            "fecha_factura_desde": "2024-01-31",
        })
        result = self.f1_obj.read(self.cursor, self.uid, f1_id, ["polissa_id"])
        self.assertEqual(result["polissa_id"][0], self.polissa_ids[1])
        self.f1_obj.write(self.cursor, self.uid, f1_id, {"fecha_factura_desde": "2024-02-29"})
        result = self.f1_obj.read(self.cursor, self.uid, f1_id, ["polissa_id"])
        self.assertEqual(result["polissa_id"][0], self.polissa_ids[2])
