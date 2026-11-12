# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestReportBackendSomEstalvi(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.pool = self.openerp.pool
        self.imd = self.pool.get('ir.model.data')
        self.report_obj = self.pool.get('report.backend.som.estalvi')
        self.polissa_obj = self.pool.get('giscedata.polissa')
        self.factura_obj = self.pool.get('giscedata.facturacio.factura')

        # Obtenim una pòlissa de test
        self.polissa_id = self.imd.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        self.maxDiff = None

    def tearDown(self):
        self.txn.stop()

    def test__get_dates__with_invoice(self):
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)

        start_date, end_date = self.report_obj.get_dates(
            self.cursor, self.uid, polissa
        )

        self.assertEqual(end_date, '2017-01-31')
        self.assertEqual(start_date, '2016-02-01')

    def test__get_titular(self):
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)

        result = self.report_obj.get_titular(
            self.cursor, self.uid, polissa
        )
        lang = self.report_obj.get_lang(self.cursor, self.uid, self.polissa_id)

        expected = {
            "nom": polissa.titular.name,
            "adreca": polissa.cups.direccio,
            "cups": polissa.cups.name,
            "peatge": polissa.tarifa.name,
            "tarifa": polissa.llista_preu.nom_comercial,
        }

        self.assertEqual(result, expected)
        self.assertEqual(polissa.titular.lang, lang)

    def test__is_printable__with_recent_invoice(self):
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)

        self.assertIsNone(self.report_obj.is_printable(self.cursor, self.uid, polissa))
