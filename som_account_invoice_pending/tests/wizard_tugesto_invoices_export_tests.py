# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import netsvc
from osv import osv

class TestWizardTugestoInvoicesExport(testing.OOTestCaseWithCursor):

    def _load_demo_data(self, cursor, uid):    
        pool = self.openerp.pool
        imd_obj = pool.get('ir.model.data') 
        self.partner_obj = pool.get('res.partner') 
        self.imd_obj = pool.get('ir.model.data')   
        self.pol_obj = pool.get('giscedata.polissa')                           
        self.pending_obj = pool.get('account.invoice.pending.state')               
        self.inv_obj = pool.get('account.invoice')        
        self.fact_obj = pool.get('giscedata.facturacio.factura')        
        self.wiz_obj = pool.get('wizard.export.tugesto.invoices')
        self.partner_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'full_partner1')[1]
        self.invoice_1_id = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio', 'factura_0001')[1]
        self.invoice_2_id = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio', 'factura_0002')[1]
        self.dp_pending_tugesto_id =  imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pending_tugesto_default_pending_state')[1]
        self.bs_pending_tugesto_id =  imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pending_tugesto_bo_social_pending_state')[1]
        self.dp_tugesto_id =  imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'tugesto_default_pending_state')[1]
        self.bs_tugesto_id =  imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'tugesto_bo_social_pending_state')[1]
        
        self.dp_1r_avis_id =  imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'default_avis_impagament_pending_state')[1]
        #self.bs_1r_avis_id =  imd_obj.get_object_reference(
        #    cursor, uid, 'giscedata_facturacio_comer_bono_social', 'avis_impagament_pending_state')[1]

    def test_tugesto_invoices_export_creates_file__ok(self):
        cursor = self.cursor
        uid = self.uid
        pool = self.openerp.pool
        self._load_demo_data(cursor, uid)
        invs_ids = [inv.invoice_id.id for inv in self.fact_obj.browse(cursor, uid, [self.invoice_1_id, self.invoice_2_id])]

        self.inv_obj.write(cursor, uid, invs_ids, {'partner_id': self.partner_id})

        wf_service = netsvc.LocalService('workflow')

        for inv_id in invs_ids:
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cursor)

        context = {'active_ids': [self.invoice_1_id, self.invoice_2_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)
        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)

        self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)

        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)
        self.assertTrue(wizard.file_bin)


    def test_tugesto_invoices_export_no_active_ids__error(self):
        cursor = self.cursor
        uid = self.uid
        self._load_demo_data(cursor, uid)
        invs_ids = [inv.invoice_id.id for inv in self.fact_obj.browse(cursor, uid, [self.invoice_1_id, self.invoice_2_id])]

        self.inv_obj.write(cursor, uid, invs_ids, {'partner_id': self.partner_id})

        wf_service = netsvc.LocalService('workflow')

        for inv_id in invs_ids:
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cursor)

        context = {'active_ids': []}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)
        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)

        self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)

        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)
        with self.assertRaises(osv.except_osv):
            #TODO: mirar que l'excepció sigui la que toca
            self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)

    def test_tugesto_invoices_export_pending_state_updated__ok(self):
        cursor = self.cursor
        uid = self.uid
        self._load_demo_data(cursor, uid)
        invs_ids = [inv.invoice_id.id for inv in self.fact_obj.browse(cursor, uid, [self.invoice_1_id, self.invoice_2_id])]

        self.inv_obj.write(cursor, uid, invs_ids, {'partner_id': self.partner_id})

        wf_service = netsvc.LocalService('workflow')

        for inv_id in invs_ids:
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cursor)
        
        inv1_id = invs_ids[0]
        inv2_id = invs_ids[1]
        

        self.pol_obj.send_signal(cursor, uid, [1], [
            'validar', 'contracte'
        ])

        context = {'active_ids': [self.invoice_1_id, self.invoice_2_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)
        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)

        self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)
        self.wiz_obj.tugesto_invoices_update_pending_state(cursor, uid, [wiz_id], context)

        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)

        inv1_ps_id = self.inv_obj.browse(cursor, uid, inv1_id).pending_state.id
        inv2_ps_id = self.inv_obj.browse(cursor, uid, inv2_id).pending_state.id

        #import pudb; pu.db
        self.assertEqual(inv1_ps_id, self.dp_1r_avis_id)
        self.assertEqual(inv2_ps_id, self.dp_1r_avis_id)

    def test_tugesto_invoices_export_pending_state_updated__error(self):
        cursor = self.cursor
        uid = self.uid
        self._load_demo_data(cursor, uid)
        invs_ids = [inv.invoice_id.id for inv in self.fact_obj.browse(cursor, uid, [self.invoice_1_id, self.invoice_2_id])]

        self.inv_obj.write(cursor, uid, invs_ids, {'partner_id': self.partner_id})

        wf_service = netsvc.LocalService('workflow')

        for inv_id in invs_ids:
            wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cursor)
        
        context = {'active_ids': [self.invoice_1_id, self.invoice_2_id]}
        wiz_id = self.wiz_obj.create(cursor, uid, {}, context)
        wizard = self.wiz_obj.browse(cursor, uid, wiz_id)

        with self.assertRaises(osv.except_osv):
            #TODO: mirar que l'excepció posi "error en l'estat pendent"
            self.wiz_obj.tugesto_invoices_export(cursor, uid, [wiz_id], context)




            
