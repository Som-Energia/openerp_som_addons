# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from destral import testing
from destral.transaction import Transaction


class SomOvInvoicesTests(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.imd = self.pool.get('ir.model.data')
        self.invoice = self.pool.get('somre.ov.invoices')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    base_vat = 'ES48591264S'
    legal_vat = 'ESW2796397D'
    base_invoice = 'F0'
    legal_invoice = 'F1'
    missing_vat = 'ES1111111HH'
    specific_retribution_type_value = '02'
    complementary_liquidation = 'COMPLEMENTARY'

    def test__get_invoices__base(self):
        vat = self.base_vat

        result = self.invoice.get_invoices(
            self.cursor, self.uid, vat, oldest_date=None)

        expected_result = [
            dict(
                contract_number='103',
                invoice_number='CO',
                concept='specific_retribution',
                emission_date='2022-09-30',
                first_period_date='2022-09-01',
                last_period_date='2022-09-30',
                amount=-4.35,
                liquidation=self.complementary_liquidation,
                payment_status='open',
            ),
            dict(
                contract_number='103',
                invoice_number='RE',
                concept='specific_retribution',
                emission_date='2022-09-30',
                first_period_date='2022-09-01',
                last_period_date='2022-09-30',
                amount=14.35,
                liquidation="03",
                payment_status='open',
            ),
            dict(
                contract_number='103',
                invoice_number='F2',
                concept='market',
                emission_date='2022-09-30',
                first_period_date='2022-09-01',
                last_period_date='2022-09-30',
                amount=29.77,
                liquidation=None,
                payment_status='paid',
            ),
            dict(
                contract_number='103',
                invoice_number='F0',
                concept='market',
                emission_date='2022-10-31',
                first_period_date='2022-10-01',
                last_period_date='2022-10-31',
                amount=28.77,
                liquidation=None,
                payment_status='open',
            ),
        ]

        self.assertEqual(expected_result, result)

    def test__get_invoices__no_draft(self):
        vat = self.legal_vat

        result = self.invoice.get_invoices(
            self.cursor, self.uid, vat, oldest_date=None)

        self.assertEqual(result, [])

    def test__get_invoices__open_and_paid(self):
        vat = self.base_vat

        result = self.invoice.get_invoices(
            self.cursor, self.uid, vat, oldest_date=None)

        self.assertEqual(len(result), 4)

    def test__get_invoices__user_not_exists(self):
        vat = self.missing_vat

        result = self.invoice.get_invoices(
            self.cursor, self.uid, vat, oldest_date=None)

        self.assertEqual(result, dict(
            code='NoSuchUser',
            error='User does not exist',
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    def test__download_invoice_pdf__user_not_exists(self):
        vat = self.missing_vat
        invoice_number = self.base_invoice

        result = self.invoice.download_invoice_pdf(
            self.cursor, self.uid, vat, invoice_number)

        self.assertEqual(result, dict(
            code='NoSuchUser',
            error='User does not exist',
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    def test__download_invoice_pdf__not_such_invoice_for_vat(self):
        vat = self.legal_vat
        invoice_number = 'No such invoice'

        result = self.invoice.download_invoice_pdf(
            self.cursor, self.uid, vat, invoice_number)

        self.assertEqual(result, dict(
            code='NoSuchInvoice',
            error="No invoice found with number 'No such invoice'",
            invoice_number='No such invoice',
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    def test__get_invoice__not_owner(self):
        invoice_number = self.legal_invoice
        vat = self.base_vat

        result = self.invoice.download_invoice_pdf(
            self.cursor, self.uid, vat, invoice_number)

        self.assertEqual(result, dict(
            code='UnauthorizedAccess',
            error="User {vat} cannot access the Invoice '{invoice_number}'".format(
                vat=vat,
                invoice_number=invoice_number
            ),
            username=vat,
            resource_type="Invoice",
            resource_name=invoice_number,
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    def test__get_liquidation_description__input_01(self):
        invoice_id = self.reference(
            'somre_ov_module', 'giscere_facturacio_factura_specific_retribution_0')

        result = self.invoice.get_liquidation_description(
            self.cursor, self.uid, "01", invoice_id)

        self.assertEqual(result, None)

    def test__get_liquidation_description__input_specific_retribution_type_value(self):
        invoice_id = self.reference(
            'somre_ov_module', 'giscere_facturacio_factura_specific_retribution_0')

        result = self.invoice.get_liquidation_description(
            self.cursor, self.uid, self.specific_retribution_type_value, invoice_id)

        self.assertEqual(result, "03")

    def test__get_liquidation_description__base(self):
        invoice_id = self.reference(
            'somre_ov_module', 'giscere_facturacio_factura_specific_retribution_0')

        result = self.invoice.get_liquidation_description(
            self.cursor, self.uid, "03", invoice_id)

        self.assertEqual(result, None)

    def test__get_liquidation_description__extraline_doest_not_exists(self):
        invoice_id = self.reference(
            'somre_ov_module', 'giscere_facturacio_factura_1')

        result = self.invoice.get_liquidation_description(
            self.cursor, self.uid, self.specific_retribution_type_value, invoice_id)

        self.assertEqual(result, None)

    def test__get_liquidation_description__complementary(self):
        invoice_id = self.reference(
            'somre_ov_module', 'giscere_facturacio_factura_specific_retribution_complementary_0')

        result = self.invoice.get_liquidation_description(
            self.cursor, self.uid, self.specific_retribution_type_value, invoice_id)

        self.assertEqual(result, self.complementary_liquidation)

    def test__get_invoices__with_oldest_date(self):
        vat = self.base_vat
        oldest_date = '2022-10-31'

        result = self.invoice.get_invoices(
            self.cursor, self.uid, vat, oldest_date=oldest_date)

        self.assertEqual(result, [
            # Invoices emitted 2022-09-30 are filtered out
            dict(
                contract_number='103',
                invoice_number='F0',
                concept='market',
                emission_date='2022-10-31',
                first_period_date='2022-10-01',
                last_period_date='2022-10-31',
                amount=28.77,
                liquidation=None,
                payment_status='open',
            ),
        ])

    def reference(self, module, id):
        return self.imd.get_object_reference(
            self.cursor, self.uid, module, id,
        )[1]
