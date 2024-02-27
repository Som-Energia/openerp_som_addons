# -*- coding: utf-8 -*-
from destral import testing
import netsvc
from osv import osv


class AccountInvoice(osv.osv):
    def _fnt_is_last(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, False)
        return res


class TestWizardTugestoInvoicesExport(testing.OOTestCaseWithCursor):
    def _load_demo_data(self, cursor, uid):
        pool = self.openerp.pool
        imd_obj = pool.get("ir.model.data")
        self.partner_obj = pool.get("res.partner")
        self.imd_obj = pool.get("ir.model.data")
        self.pol_obj = pool.get("giscedata.polissa")
        self.pending_obj = pool.get("account.invoice.pending.state")
        self.inv_obj = pool.get("account.invoice")
        self.fact_obj = pool.get("giscedata.facturacio.factura")
        self.wiz_obj = pool.get("wizard.export.tugesto.invoices")
        self.partner_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "full_partner1"
        )[1]
        self.polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0001"
        )[1]
        self.invoice_1_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]
        self.invoice_2_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0002"
        )[1]
        self.dp_pending_tugesto_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "pending_tugesto_default_pending_state"
        )[1]
        self.bs_pending_tugesto_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "pending_tugesto_bo_social_pending_state"
        )[1]
        self.dp_tugesto_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "tugesto_default_pending_state"
        )[1]
        self.bs_tugesto_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "tugesto_bo_social_pending_state"
        )[1]

        self.dp_1r_avis_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "default_avis_impagament_pending_state"
        )[1]
        # self.bs_1r_avis_id =  imd_obj.get_object_reference(
        #     cursor,
        #     uid,
        #     'giscedata_facturacio_comer_bono_social',
        #     'avis_impagament_pending_state',
        # )[1]

    def _load_data_unpaid_invoices(self, cursor, uid, invoice_semid_list=[]):
        contract_name = ""
        for index, res_id in enumerate(invoice_semid_list, start=1):
            fact_id = self.imd_obj.get_object_reference(
                cursor, uid, "giscedata_facturacio", "factura_000" + str(index)
            )[1]
            invoice_id = self.fact_obj.read(cursor, uid, fact_id, ["invoice_id"])["invoice_id"][0]

            if index == 1:
                contract_name = self.inv_obj.read(cursor, uid, invoice_id, ["name"])["name"]

            self.inv_obj.write(
                cursor,
                uid,
                invoice_id,
                {
                    "name": contract_name,
                },
            )
            self.inv_obj.set_pending(cursor, uid, [invoice_id], res_id)

    def test_tugesto_invoices_export_creates_file__ok(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_demo_data(cursor, uid)
        self._load_data_unpaid_invoices(
            cursor, uid, [self.bs_pending_tugesto_id, self.bs_pending_tugesto_id]
        )

        context = {"active_ids": [self.invoice_1_id, self.invoice_2_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)

        self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)
        self.wiz_obj.tugesto_invoices_update_pending_state(cursor, uid, [wiz_id], context)

        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)
        self.assertTrue(wizard.file_bin)

    def test_tugesto_invoices_export_no_active_ids__error(self):
        cursor = self.cursor
        uid = self.uid
        self._load_demo_data(cursor, uid)
        invs_ids = [
            inv.invoice_id.id
            for inv in self.fact_obj.browse(cursor, uid, [self.invoice_1_id, self.invoice_2_id])
        ]

        self.inv_obj.write(cursor, uid, invs_ids, {"partner_id": self.partner_id})

        wf_service = netsvc.LocalService("workflow")

        for inv_id in invs_ids:
            wf_service.trg_validate(uid, "account.invoice", inv_id, "invoice_open", cursor)

        context = {"active_ids": []}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)

        with self.assertRaises(osv.except_osv) as e:
            self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)

        self.assertEqual(e.exception.value, u"No s'ha seleccionat cap factura")

    def test_tugesto_invoices_export_pending_state_updated__ok(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_demo_data(cursor, uid)
        self._load_data_unpaid_invoices(
            cursor, uid, [self.bs_pending_tugesto_id, self.bs_pending_tugesto_id]
        )

        context = {"active_ids": [self.invoice_1_id, self.invoice_2_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)

        self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)
        self.wiz_obj.tugesto_invoices_update_pending_state(cursor, uid, [wiz_id], context)

        inv_data = self.fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.bs_tugesto_id)

        inv_data = self.fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.bs_tugesto_id)

    def test_tugesto_invoices_export_pending_state_updated__error(self):
        cursor = self.cursor
        uid = self.uid
        self._load_demo_data(cursor, uid)
        invs_ids = [
            inv.invoice_id.id
            for inv in self.fact_obj.browse(cursor, uid, [self.invoice_1_id, self.invoice_2_id])
        ]

        self.inv_obj.write(cursor, uid, invs_ids, {"partner_id": self.partner_id})

        wf_service = netsvc.LocalService("workflow")

        for inv_id in invs_ids:
            wf_service.trg_validate(uid, "account.invoice", inv_id, "invoice_open", cursor)

        context = {"active_ids": [self.invoice_1_id, self.invoice_2_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)

        with self.assertRaises(osv.except_osv) as e:
            self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)

        self.assertEqual(
            e.exception.value, u"L'estat pendent d'alguna de les factures no és l'esperat"
        )
