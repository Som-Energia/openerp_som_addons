# -*- coding: utf-8 -*-
import unittest
from destral import testing
from destral.transaction import Transaction
import netsvc
from datetime import datetime, timedelta, date
from osv import osv, fields
from osv.orm import ValidateException
from osv.osv import except_osv

class ResPartnerTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.Investment = self.openerp.pool.get('generationkwh.investment')
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.ResPartner = self.openerp.pool.get('res.partner')
        self.Invoice = self.openerp.pool.get('account.invoice')
        self.Factura = self.openerp.pool.get('giscedata.facturacio.factura')
        self.Polissa = self.openerp.pool.get('giscedata.polissa')

    def tearDown(self):
        self.txn.stop()

    def test_cancel_member_with_active_generation__notAllowed(self):
        invest_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'genkwh_0001'
            )[1]
        investment = self.Investment.browse(self.cursor, self.uid, invest_id)
        investment.write({'last_effective_date':'15/03/3000'})
        partner_id = investment.member_id.partner_id.id

        with self.assertRaises(except_osv) as ctx:
            self.ResPartner.verifica_baixa_soci(self.cursor, self.uid, partner_id)

        self.assertEqual(ctx.exception.message,
            "warning -- El soci no pot ser donat de baixa!\n\nEl soci té inversions de generation actives.")

    def test_cancel_member_with_active_apo__notAllowed(self):
        invest_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'apo_0001'
            )[1]
        investment = self.Investment.browse(self.cursor, self.uid, invest_id)
        member_id = investment.member_id.id
        partner_id = investment.member_id.partner_id.id
        investment.write({'last_effective_date': False})
        generation_invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id),('emission_id','=',1)])
        self.Investment.write(self.cursor, self.uid, generation_invs, {'active':False})

        with self.assertRaises(except_osv) as ctx:
            self.ResPartner.verifica_baixa_soci(self.cursor, self.uid, partner_id)

        self.assertEqual(ctx.exception.message,
            "warning -- El soci no pot ser donat de baixa!\n\nEl soci té aportacions actives.")
    
    def test_cancel_member_with_pending_invoices__notAllowed(self):
        fact_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio', 'factura_0001'
            )[1]
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1' 
            )[1]
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001' 
            )[1]
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])
        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        invoice_id = self.Factura.read(self.cursor, self.uid, fact_id, ['invoice_id'])['invoice_id'][0]
        self.Invoice.write(self.cursor, self.uid, invoice_id, {'partner_id': partner_id,
                                                       'state': 'open'})
    
        with self.assertRaises(except_osv) as ctx:
            self.ResPartner.verifica_baixa_soci(self.cursor, self.uid, partner_id)

        self.assertEqual(ctx.exception.message,
            "warning -- El soci no pot ser donat de baixa!\n\nEl soci té factures pendents.")

    def test_cancel_member_with_active_contract__notAllowed(self):
        fact_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio', 'factura_0001'
            )[1]
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1' 
            )[1]
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001' 
            )[1]
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])
        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        
        self.Polissa.write(self.cursor, self.uid, [polissa_id], {'titular': partner_id})
    
        with self.assertRaises(except_osv) as ctx:
            self.ResPartner.verifica_baixa_soci(self.cursor, self.uid, partner_id)

        self.assertEqual(ctx.exception.message,
            "warning -- El soci no pot ser donat de baixa!\n\nEl soci té al menys un contracte actiu.")


       

