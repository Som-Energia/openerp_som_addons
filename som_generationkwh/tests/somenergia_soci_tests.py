# -*- coding: utf-8 -*-
import unittest
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
from datetime import datetime, timedelta, date
from osv import osv, fields
from osv.orm import ValidateException
from osv.osv import except_osv
import mock
import som_polissa_soci
import mailchimp_marketing

class SomenergiaSociTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.Investment = self.openerp.pool.get('generationkwh.investment')
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.ResPartner = self.openerp.pool.get('res.partner')
        self.ResPartnerAddress = self.openerp.pool.get('res.partner.address')
        self.Invoice = self.openerp.pool.get('account.invoice')
        self.Factura = self.openerp.pool.get('giscedata.facturacio.factura')
        self.Polissa = self.openerp.pool.get('giscedata.polissa')
        self.Soci = self.openerp.pool.get('somenergia.soci')
        self.PaymentOrder = self.openerp.pool.get('payment.order')
        self.WizPayRemesa = self.openerp.pool.get('pagar.remesa.wizard')

        self.bank_account_id = 1  # just for tests

    def tearDown(self):
        self.txn.stop()

    def test_cancel_member_with_active_generation__notAllowed(self):
        invest_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'genkwh_0001'
            )[1]
        investment = self.Investment.browse(self.cursor, self.uid, invest_id)
        today = date.today()
        future_date = (today + timedelta(days=365)).strftime('%Y-%m-%d')
        investment.write({'last_effective_date': future_date})
        member_id = investment.member_id.id
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})

        with self.assertRaises(except_osv) as ctx:
            self.Soci.do_baixa_soci(self.cursor, self.uid, member_id, self.bank_account_id)

        self.assertIn("El soci té inversions de generation actives", ctx.exception.message)

    def test_cancel_member_with_active_apo__notAllowed(self):
        invest_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'apo_0003'
            )[1]
        investment = self.Investment.browse(self.cursor, self.uid, invest_id)
        member_id = investment.member_id.id
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        investment.write({'last_effective_date': False, 'draft': False})
        generation_invs = self.Investment.search(
            self.cursor, self.uid, [('member_id','=', member_id),('emission_id','=',1)])
        self.Investment.write(self.cursor, self.uid, generation_invs, {'active':False})

        with self.assertRaises(except_osv) as ctx:
            self.Soci.do_baixa_soci(self.cursor, self.uid, member_id, self.bank_account_id)

        self.assertIn("El soci té aportacions actives", ctx.exception.message)
    
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
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})

        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])
        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        invoice_id = self.Factura.read(
            self.cursor, self.uid, fact_id, ['invoice_id'])['invoice_id'][0]
        self.Invoice.write(
            self.cursor, self.uid, invoice_id, {'partner_id': partner_id, 'state': 'open'})
    
        with self.assertRaises(except_osv) as ctx:
            self.Soci.do_baixa_soci(self.cursor, self.uid, member_id, self.bank_account_id)

        self.assertIn("El soci té factures pendents", ctx.exception.message)

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_members_lists")  # noqa: E501
    def test_cancel_member_with_active_contract__Allowed(self, mailchimp_mock):
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
            )[1]
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])

        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        self.Polissa.write(self.cursor, self.uid, [polissa_id], {'titular': partner_id})

        self.assertEqual(
            self.Soci.do_baixa_soci(self.cursor, self.uid, member_id, self.bank_account_id), True)
        partner_id = self.Soci.read(
            self.cursor, self.uid, member_id, ['partner_id'])['partner_id'][0]
        mailchimp_mock.assert_called_with(self.cursor, self.uid, [partner_id], context={})

    def test_cancel_member_with_related_contract__notAllowed(self):
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
            )[1]
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])

        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        self.Polissa.write(self.cursor, self.uid, [polissa_id], {'soci': partner_id})

        with self.assertRaises(except_osv) as ctx:
            self.Soci.do_baixa_soci(self.cursor, self.uid, member_id, self.bank_account_id)

        self.assertIn("El soci té al menys un contracte vinculat", ctx.exception.message)

    def test_cancel_member_with_sponsored_contract__notAllowed(self):
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
        )[1]
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1'
        )[1]
        sponsored_partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_noinversor2'
        )[1]
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])

        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        self.Polissa.write(self.cursor, self.uid, [polissa_id], {
            'soci': partner_id, 'titular': sponsored_partner_id
        })

        res = self.Soci.get_baixa_blocking_reasons(self.cursor, self.uid, member_id)

        self.assertEqual(res, ["El soci té al menys un contracte apadrinat."])

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_members_lists")  # noqa: E501
    def test_cancel_member_with_sponsored_contract_with_context__Allowed(self, mailchimp_mock):
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
        )[1]
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1'
        )[1]
        sponsored_partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_noinversor2'
        )[1]
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])

        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        self.Polissa.write(self.cursor, self.uid, [polissa_id], {
            'soci': partner_id, 'titular': sponsored_partner_id
        })

        self.Soci.do_baixa_soci(
            self.cursor, self.uid, member_id,
            self.bank_account_id, context={'skip_sponsored_check': True}
        )

        polissa = self.Polissa.browse(self.cursor, self.uid, polissa_id)
        self.assertFalse(polissa.soci)
        self.assertEqual(polissa.state, 'esborrany')
        self.assertEqual(polissa.titular.id, sponsored_partner_id)
        self.assertIn('treiem apadrinament', polissa.titular.comment)
        mailchimp_mock.assert_called_with(
            self.cursor, self.uid, [partner_id], context={'skip_sponsored_check': True})

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_members_lists")  # noqa: E501
    def test_cancel_member_with_active_contract_creates_payment_order(self, mailchimp_mock):
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
            )[1]
        return_payment_mode_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_return_payment_mode'
        )[1]
        self.Soci.write(
            self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])

        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        self.Polissa.write(self.cursor, self.uid, [polissa_id], {'titular': partner_id})

        payment_order_ids = self.PaymentOrder.search(
            self.cursor, self.uid, [('mode', '=', return_payment_mode_id)])
        self.assertEqual(len(payment_order_ids), 0)

        self.assertEqual(
            self.Soci.do_baixa_soci(self.cursor, self.uid, member_id, self.bank_account_id), True)
        partner_id = self.Soci.read(
            self.cursor, self.uid, member_id, ['partner_id'])['partner_id'][0]
        mailchimp_mock.assert_called_with(self.cursor, self.uid, [partner_id], context={})

        payment_order_ids = self.PaymentOrder.search(
            self.cursor, self.uid, [('mode', '=', return_payment_mode_id)])
        self.assertEqual(len(payment_order_ids), 1)
        payment_order_id = payment_order_ids[0]
        payment_order = self.PaymentOrder.browse(self.cursor, self.uid, payment_order_id)
        self.assertEqual(payment_order.state, 'draft')
        self.assertEqual(payment_order.total, 100)
