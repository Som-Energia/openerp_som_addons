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

