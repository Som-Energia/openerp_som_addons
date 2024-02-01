# -*- coding: utf-8 -*-
from destral import testing
import unittest
from destral.transaction import Transaction
from expects import *


class WizardCreateTechnicalReportTests(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip(reason="WIP")
    def test__get_data__InvoiceF1NG_invoice20TD(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        cursor = self.cursor
        uid = self.uid
        polissa_id = imd_obj.get_object_reference(cursor, uid, "giscedata_polissa", "polissa_0001")[
            1
        ]
        invoice_id = imd_obj.get_object_reference(cursor, uid, "som_informe", "factura_0067")[1]
        ctx = {
            "active_id": polissa_id,
            "active_ids": [polissa_id],
        }
        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        invoice = fact_obj.browse(cursor, uid, invoice_id)
        extractor = wiz_obj.factory_metadata_extractor("InvoiceF1NG")

        result = extractor.get_data(cursor, uid, wiz, invoice)

        self.assertEqual(
            result,
            {
                "invoice_type": u"N",
                "date_from": "15-08-2021",
                "amount_base": 10.0,
                "invoice_date": "01-10-2021",
                "invoiced_days": 32,
                "date_to": "15-09-2021",
                "date": "2021-10-01",
                "invoice_number": u"12345678",
                "numero_edm": u"004007",
                "type": "InvoiceF1NG",
                "invoiced_energy": 1.0,
                "amount_total": 10.0,
            },
        )

    @unittest.skip(reason="WIP")
    def test__get_data__InvoiceF1NG_invoice30TD(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        cursor = self.cursor
        uid = self.uid
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_tarifa_019"
        )[1]
        invoice_id = imd_obj.get_object_reference(cursor, uid, "som_informe", "factura_0068_30TD")[
            1
        ]
        ctx = {
            "active_id": polissa_id,
            "active_ids": [polissa_id],
        }
        wiz_id = wiz_obj.create(cursor, uid, {}, context=ctx)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)
        invoice = fact_obj.browse(cursor, uid, invoice_id)
        extractor = wiz_obj.factory_metadata_extractor("InvoiceF1NG")

        result = extractor.get_data(cursor, uid, wiz, invoice)

        self.assertEqual(
            result,
            {
                "invoice_type": u"N",
                "date_from": "15-08-2021",
                "amount_base": 10.0,
                "invoice_date": "16-09-2021",
                "invoiced_days": 32,
                "date_to": "15-09-2021",
                "date": "2021-09-16",
                "invoice_number": u"12345679",
                "numero_edm": u"004008",
                "type": "InvoiceF1NG",
                "invoiced_energy": 1.0,
                "amount_total": 10.0,
            },
        )
