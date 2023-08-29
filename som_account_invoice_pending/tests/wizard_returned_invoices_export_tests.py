# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from osv.osv import except_osv


class TestWizardReturnedInvoicesExport(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool

    def _load_demo_data(self, cursor, uid):
        imd_obj = self.pool.get("ir.model.data")
        self.imd_obj = self.pool.get("ir.model.data")
        self.pending_obj = self.pool.get("account.invoice.pending.state")
        self.inv_obj = self.pool.get("account.invoice")
        self.fact_obj = self.pool.get("giscedata.facturacio.factura")
        self.wiz_obj = self.pool.get("wizard.export.returned.invoices")
        self.invoice_1_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]
        self.invoice_2_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0002"
        )[1]

    def test__returned_invoices_export_without_phone__wontWork(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self._load_demo_data(cursor, uid)

            factura = self.fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.inv_obj.set_pending(cursor, uid, [factura.invoice_id.id], 1)
            partner = factura.partner_id
            adreces = [item.id for item in partner.address]
            self.pool.get("res.partner.address").write(
                cursor, uid, adreces, {"mobile": False, "phone": False}
            )

            context = {"active_ids": [self.invoice_1_id, self.invoice_2_id]}
            with self.assertRaises(except_osv):
                wiz_id = self.wiz_obj.create(cursor, uid, {})
                self.wiz_obj.browse(cursor, uid, wiz_id)
                self.wiz_obj.returned_invoices_export(cursor, uid, [wiz_id], context=context)
