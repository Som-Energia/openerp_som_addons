# -*- coding: utf-8 -*-

from destral import testing
import netsvc
from osv import osv
from account_invoice_som.wizard import wizard_payment_order_add_invoices
import mock


class TestJob:
    def work(self):
        return True

    def __init__(self):
        self.id = 0


class TestAutoWorker:
    def work(self):
        return True


class AccountInvoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"

    def afegeix_a_remesa_async(self, cursor, uid, ids, order_id, context=None):
        self.afegeix_a_remesa(cursor, uid, ids, order_id, context=context)
        return TestJob()  # Fake test job


AccountInvoice()


class TestsWizardPaymentOrderAddInvoices(testing.OOTestCaseWithCursor):
    def test_add_invoices_to_payment_order__empty_filters_ok(self):
        wiz_obj = self.openerp.pool.get("wizard.payment.order.add.invoices")
        inv_obj = self.openerp.pool.get("account.invoice")
        cursor = self.cursor
        uid = self.uid
        wiz_id = wiz_obj.create(cursor, uid, {})
        wizard = wiz_obj.browse(cursor, uid, wiz_id)
        values = {"init_date": "", "end_date": "", "invoice_state": "", "invoice_type": ""}
        wizard.write(values)

        wizard.add_invoices_to_payment_order()

        all_invoices = inv_obj.search(cursor, uid, [("payment_order_id", "=", False)])
        self.assertEqual(
            "La cerca ha trobat {} resultats".format(len(all_invoices)), wizard.len_result
        )

    @mock.patch.object(wizard_payment_order_add_invoices, "create_jobs_group")
    @mock.patch.object(wizard_payment_order_add_invoices, "AutoWorker")
    def test_add_invoices_to_payment_order__out_invoices_ok(
        self, mock_autoworker_class, mock_create_jobs_group
    ):
        wiz_obj = self.openerp.pool.get("wizard.payment.order.add.invoices")
        inv_obj = self.openerp.pool.get("account.invoice")
        po_obj = self.openerp.pool.get("payment.order")
        imd_obj = self.openerp.pool.get("ir.model.data")
        cursor = self.cursor
        uid = self.uid
        order_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account_invoice_som", "remesa_0001"
        )[1]
        search_params = [
            ("date_due", "<=", "2021-04-30"),
            ("date_due", ">=", "2021-01-01"),
            ("type", "=", "out_invoice"),
        ]
        inv_ids = inv_obj.search(cursor, uid, search_params + [("state", "=", "draft")])
        wf_service = netsvc.LocalService("workflow")
        for inv_id in inv_ids:
            wf_service.trg_validate(uid, "account.invoice", inv_id, "invoice_open", cursor)
        inv_ids = inv_obj.search(cursor, uid, search_params + [("state", "=", "open")])

        wiz_id = wiz_obj.create(cursor, uid, {})
        wizard = wiz_obj.browse(cursor, uid, wiz_id)
        values = {
            "init_date": "2021-01-01",
            "end_date": "2021-04-30",
            "order": order_id,
            "invoice_type": "out_invoice",
        }
        wizard.write(values)

        # Do not create autoworkers
        mock_autoworker_class.return_value = TestAutoWorker()
        mock_create_jobs_group.return_value = True

        wizard.add_invoices_to_payment_order()
        wizard.add_invoices_with_limit()

        order = po_obj.browse(cursor, uid, order_id)
        self.assertEqual(len(inv_ids), len(order.line_ids))

    @mock.patch.object(wizard_payment_order_add_invoices, "create_jobs_group")
    @mock.patch.object(wizard_payment_order_add_invoices, "AutoWorker")
    def test_add_invoices_to_payment_order__in_invoices_ok(
        self, mock_autoworker_class, mock_create_jobs_group
    ):
        wiz_obj = self.openerp.pool.get("wizard.payment.order.add.invoices")
        inv_obj = self.openerp.pool.get("account.invoice")
        po_obj = self.openerp.pool.get("payment.order")
        imd_obj = self.openerp.pool.get("ir.model.data")
        cursor = self.cursor
        uid = self.uid
        order_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account_invoice_som", "remesa_0002"
        )[1]
        search_params = [
            ("date_due", "<=", "2021-04-30"),
            ("date_due", ">=", "2021-01-01"),
            ("type", "=", "in_invoice"),
        ]
        inv_ids = inv_obj.search(cursor, uid, search_params + [("state", "=", "draft")])
        wf_service = netsvc.LocalService("workflow")
        for inv_id in inv_ids:
            inv = inv_obj.browse(cursor, uid, inv_id)
            inv.write({"check_total": inv.amount_total})
        for inv_id in inv_ids:
            wf_service.trg_validate(uid, "account.invoice", inv_id, "invoice_open", cursor)
        inv_ids = inv_obj.search(cursor, uid, search_params + [("state", "=", "open")])
        wiz_id = wiz_obj.create(cursor, uid, {})
        wizard = wiz_obj.browse(cursor, uid, wiz_id)
        values = {
            "init_date": "2021-01-01",
            "end_date": "2021-04-30",
            "order": order_id,
            "invoice_type": "in_invoice",
        }
        wizard.write(values)

        # Do not create autoworkers
        mock_autoworker_class.return_value = TestAutoWorker()
        mock_create_jobs_group.return_value = True

        wizard.add_invoices_to_payment_order()
        wizard.add_invoices_with_limit()

        order = po_obj.browse(cursor, uid, order_id)

        self.assertTrue(len(inv_ids) == len(order.line_ids))

    def test_add_invoices_to_payment_order__ag_invoices_ok(self):
        wiz_obj = self.openerp.pool.get("wizard.payment.order.add.invoices")
        inv_obj = self.openerp.pool.get("account.invoice")
        self.openerp.pool.get("payment.order")
        imd_obj = self.openerp.pool.get("ir.model.data")
        cursor = self.cursor
        uid = self.uid
        order_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account_invoice_som", "remesa_0001"
        )[1]
        search_params = [
            ("date_due", "<=", "2021-04-30"),
            ("date_due", ">=", "2021-01-01"),
            ("type", "=", "out_invoice"),
        ]
        inv_ids = inv_obj.search(cursor, uid, search_params + [("state", "=", "draft")])
        wf_service = netsvc.LocalService("workflow")
        for inv_id in inv_ids:
            wf_service.trg_validate(uid, "account.invoice", inv_id, "invoice_open", cursor)
        inv_ids = inv_obj.search(cursor, uid, search_params + [("state", "=", "open")])
        inv = inv_obj.browse(cursor, uid, inv_ids[0])
        inv.write({"group_move_id": 1})
        wiz_id = wiz_obj.create(cursor, uid, {})
        wizard = wiz_obj.browse(cursor, uid, wiz_id)
        values = {
            "init_date": "2021-01-01",
            "end_date": "2021-04-30",
            "order": order_id,
            "invoice_type": "out_invoice",
            "allow_grouped": False,
        }
        wizard.write(values)
        wizard.add_invoices_to_payment_order()
        self.assertTrue(len(wizard.res_ids) < len(inv_ids))

        values.update({"allow_grouped": True})
        wizard.write(values)
        wizard = wiz_obj.browse(cursor, uid, wiz_id)
        wizard.add_invoices_to_payment_order()
        self.assertEqual(len(wizard.res_ids), len(inv_ids))
