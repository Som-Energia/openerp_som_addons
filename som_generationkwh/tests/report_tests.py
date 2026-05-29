# -*- coding: utf-8 -*-
from destral import testing


class ReportTests(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.ai_obj = self.openerp.pool.get("account.invoice")
        self.rp_obj = self.openerp.pool.get('res.partner')
        self.imd_obj = self.openerp.pool.get('ir.model.data')
        super(ReportTests, self).setUp()

    def test__report_retencions_data__apo(self):
        cursor = self.cursor
        uid = self.uid
        partner_id = self.imd_obj.get_object_reference(
            cursor, uid, 'som_generationkwh', 'soci_aportacions_res_partner'
        )[1]

        report_data = self.rp_obj.report_retencions_data(cursor, uid, [partner_id])

        self.assertEqual(report_data.balance, 1000)

    def test__report_retencions_data__gkwh(self):
        cursor = self.cursor
        uid = self.uid
        partner_id = self.imd_obj.get_object_reference(
            cursor, uid, 'som_generationkwh', 'res_partner_generation'
        )[1]

        report_data = self.rp_obj.report_retencions_data(cursor, uid, [partner_id], is_generationkwh=True)

        self.assertEqual(report_data.balance, 500)

    def test__report_retencions_data__gkwh_with_amortizations(self):
        cursor = self.cursor
        uid = self.uid
        partner_id = self.imd_obj.get_object_reference(
            cursor, uid, 'som_generationkwh', 'res_partner_generation'
        )[1]

        report_data = self.rp_obj.report_retencions_data(cursor, uid, [partner_id], is_generationkwh=True)
        self.assertEqual(report_data.balance, 500)

        # Create amortization invoice
        current_year = int(report_data.year) + 1

        amor_product_id = self.imd_obj.get_object_reference(cursor, uid, 'som_generationkwh', 'genkwh_product_amortization')[1]

        invoice_vals = {
            'name': 'GKWH00003-AMOR',
            'origin': 'GKWH00003',
            'address_invoice_id': self.imd_obj.get_object_reference(cursor, uid, 'som_generationkwh', 'res_partner_address_generation')[1],
            'partner_id': partner_id,
            'date_invoice': '{}-06-01'.format(current_year),
            'state': 'open',
            'journal_id': self.imd_obj.get_object_reference(cursor, uid, 'account', 'sales_journal')[1],
            'account_id': self.imd_obj.get_object_reference(cursor, uid, 'account', 'a_recv')[1],
            'invoice_line': [(0, 0, {
                'name': 'Amortization',
                'product_id': amor_product_id,
                'price_unit': 150.0,
                'quantity': 1,
                'account_id': self.imd_obj.get_object_reference(cursor, uid, 'account', 'a_recv')[1],
            })]
        }
        self.ai_obj.create(cursor, uid, invoice_vals)

        report_data_after = self.rp_obj.report_retencions_data(cursor, uid, [partner_id], is_generationkwh=True)
        self.assertEqual(report_data_after.balance, 500 + 150)

    def test__report_retencions_data__apo_with_amortizations(self):
        cursor = self.cursor
        uid = self.uid
        partner_id = self.imd_obj.get_object_reference(
            cursor, uid, 'som_generationkwh', 'soci_aportacions_res_partner'
        )[1]

        report_data = self.rp_obj.report_retencions_data(cursor, uid, [partner_id])
        self.assertEqual(report_data.balance, 1000)

        current_year = int(report_data.year) + 1

        amor_product_id = self.imd_obj.get_object_reference(cursor, uid, 'som_generationkwh', 'genkwh_product_amortization')[1]

        invoice_vals = {
            'name': 'APO00003-AMOR',
            'origin': 'APO00003',
            'partner_id': partner_id,
            'address_invoice_id': self.imd_obj.get_object_reference(cursor, uid, 'som_generationkwh', 'res_partner_address_generation')[1],
            'date_invoice': '{}-06-01'.format(current_year),
            'state': 'open',
            'journal_id': self.imd_obj.get_object_reference(cursor, uid, 'account', 'sales_journal')[1],
            'account_id': self.imd_obj.get_object_reference(cursor, uid, 'account', 'a_recv')[1],
            'invoice_line': [(0, 0, {
                'name': 'Amortization APO',
                'product_id': amor_product_id,
                'price_unit': 300.0,
                'quantity': 1,
                'account_id': self.imd_obj.get_object_reference(cursor, uid, 'account', 'a_recv')[1],
            })]
        }
        self.ai_obj.create(cursor, uid, invoice_vals)

        report_data_after = self.rp_obj.report_retencions_data(cursor, uid, [partner_id])
        self.assertEqual(report_data_after.balance, 1000 + 300)

