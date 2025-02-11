# -*- coding: utf-8 -*-
import unittest
from destral import testing
from destral.transaction import Transaction
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
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})

        with self.assertRaises(except_osv) as ctx:
            self.Soci.verifica_baixa_soci(self.cursor, self.uid, member_id)

        self.assertEqual(ctx.exception.message,
            "warning -- El soci no pot ser donat de baixa!\n\nEl soci té inversions de generation actives.")

    def test_cancel_member_with_active_apo__notAllowed(self):
        invest_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'apo_0003'
            )[1]
        investment = self.Investment.browse(self.cursor, self.uid, invest_id)
        member_id = investment.member_id.id
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        investment.write({'last_effective_date': False, 'draft': False})
        generation_invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id),('emission_id','=',1)])
        self.Investment.write(self.cursor, self.uid, generation_invs, {'active':False})

        with self.assertRaises(except_osv) as ctx:
            self.Soci.verifica_baixa_soci(self.cursor, self.uid, member_id)

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
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})

        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])
        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        invoice_id = self.Factura.read(self.cursor, self.uid, fact_id, ['invoice_id'])['invoice_id'][0]
        self.Invoice.write(self.cursor, self.uid, invoice_id, {'partner_id': partner_id,
                                                       'state': 'open'})
    
        with self.assertRaises(except_osv) as ctx:
            self.Soci.verifica_baixa_soci(self.cursor, self.uid, member_id)

        self.assertEqual(ctx.exception.message,
            "warning -- El soci no pot ser donat de baixa!\n\nEl soci té factures pendents.")

    def test_cancel_member_with_active_contract__Allowed(self):
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
            )[1]
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])

        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        self.Polissa.write(self.cursor, self.uid, [polissa_id], {'titular': partner_id})

        self.assertEqual(self.Soci.verifica_baixa_soci(self.cursor, self.uid, member_id), True)

    def test_cancel_member_with_related_contract__notAllowed(self):
        partner_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
            )[1]
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        invs = self.Investment.search(self.cursor, self.uid, [('member_id','=', member_id)])

        self.Investment.write(self.cursor, self.uid, invs, {'active':False})

        polissa_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        self.Polissa.write(self.cursor, self.uid, [polissa_id], {'soci': partner_id})

        with self.assertRaises(except_osv) as ctx:
            self.Soci.verifica_baixa_soci(self.cursor, self.uid, member_id)

        self.assertEqual(ctx.exception.message,
            "warning -- El soci no pot ser donat de baixa!\n\nEl soci té al menys un contracte vinculat.")


    @mock.patch("som_polissa_soci.res_partner_address.ResPartnerAddress.archieve_mail_in_list")
    @mock.patch("som_polissa_soci.res_partner_address.ResPartnerAddress.get_mailchimp_list_id")
    @mock.patch.object(mailchimp_marketing, "Client")
    def test__arxiva_socia_mailchimp__withAddress(self, mock_mailchimp_client, mock_get_list_id, mock_archieve):
        soci_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
            )[1]
        partner_id = self.Soci.read(self.cursor, self.uid, soci_id, ['partner_id'])['partner_id'][0]
        address_list = self.ResPartner.read(self.cursor, self.uid, partner_id, ['address'])['address']

        mock_get_list_id.return_value = 'id'
        mock_mailchimp_client.return_value = 'MAILCHIMP_CLIENT'

        self.Soci.arxiva_socia_mailchimp(self.cursor, self.uid, soci_id)

        mock_archieve.assert_called_with(self.cursor, self.uid, address_list, 'id', 'MAILCHIMP_CLIENT')

    @mock.patch("som_polissa_soci.res_partner_address.ResPartnerAddress.archieve_mail_in_list")
    @mock.patch("som_polissa_soci.res_partner_address.ResPartnerAddress.get_mailchimp_list_id")
    @mock.patch.object(mailchimp_marketing, "Client")
    def test__arxiva_socia_mailchimp__withManyAddress(self, mock_mailchimp_client, mock_get_list_id, mock_archieve):
        soci_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
            )[1]
        partner_id = self.Soci.read(self.cursor, self.uid, soci_id, ['partner_id'])['partner_id'][0]
        address_list = self.ResPartner.read(self.cursor, self.uid, partner_id, ['address'])['address']
        other_address_id = self.ResPartnerAddress.search(self.cursor, self.uid, [('partner_id', '!=', partner_id)])[0]
        self.ResPartnerAddress.write(self.cursor, self.uid, other_address_id, {'partner_id': partner_id, 'email':'other@mail.com'})

        mock_get_list_id.return_value = 'id'
        mock_mailchimp_client.return_value = 'MAILCHIMP_CLIENT'

        self.Soci.arxiva_socia_mailchimp(self.cursor, self.uid, soci_id)

        address_list.append(other_address_id)
        mock_archieve.assert_called_with(self.cursor, self.uid, sorted(address_list), 'id', 'MAILCHIMP_CLIENT')

    @mock.patch("som_polissa_soci.res_partner_address.ResPartnerAddress.archieve_mail_in_list")
    @mock.patch("som_polissa_soci.res_partner_address.ResPartnerAddress.get_mailchimp_list_id")
    @mock.patch.object(mailchimp_marketing, "Client")
    def test__arxiva_socia_mailchimp__withoutMail(self, mock_mailchimp_client, mock_get_list_id, mock_archieve):
        #agafem un soci que no té email
        soci_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0003'
            )[1]
        partner_id = self.Soci.read(self.cursor, self.uid, soci_id, ['partner_id'])['partner_id'][0]
        address_list = self.ResPartner.read(self.cursor, self.uid, partner_id, ['address'])['address']
        mock_get_list_id.return_value = 'id'
        mock_mailchimp_client.return_value = 'MAILCHIMP_CLIENT'

        self.Soci.arxiva_socia_mailchimp(self.cursor, self.uid, soci_id)

        mock_archieve.assert_called_with(self.cursor, self.uid, address_list,  'id', 'MAILCHIMP_CLIENT')

