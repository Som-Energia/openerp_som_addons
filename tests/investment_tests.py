# -*- coding: utf-8 -*-
import unittest
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
import time
import random
from generationkwh.testutils import assertNsEqual
from datetime import datetime, timedelta, date
from yamlns import namespace as ns
import generationkwh.investmentmodel as gkwh
from osv import osv, fields
from ..investment_strategy import (
    PartnerException, InvestmentException,
    AportacionsActions)
from freezegun import freeze_time
import mock
from osv.osv import except_osv

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def send_sii_sync(self, cursor, uid, inv_id, context=None):
        return None

AccountInvoice()

class InvestmentTests(testing.OOTestCase):

    def setUp(self):
        self.MailMockup = self.openerp.pool.get('generationkwh.mailmockup')
        self.PEAccounts = self.openerp.pool.get('poweremail.core_accounts')
        self.Investment = self.openerp.pool.get('generationkwh.investment')
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.Partner = self.openerp.pool.get('res.partner')
        self.PartnerAddress = self.openerp.pool.get('res.partner.address')
        self.Invoice = self.openerp.pool.get('account.invoice')
        self.InvoiceLine = self.openerp.pool.get('account.invoice.line')
        self.Emission = self.openerp.pool.get('generationkwh.emission')
        self.PaymentLine = self.openerp.pool.get('payment.line')
        self.PaymentOrder = self.openerp.pool.get('payment.order')
        self.Soci = self.openerp.pool.get('somenergia.soci')
        self.Product = self.openerp.pool.get('product.product')
        self.AccountAccount = self.openerp.pool.get('account.account')
        self.IrProperty = self.openerp.pool.get('ir.property')
        self.maxDiff = None


    def tearDown(self):
        pass

    assertNsEqual=assertNsEqual

    def assertInvoiceInfoEqual(self, cursor, uid, invoice_id, expected):
        def proccesLine(line):
            line = ns(line)
            line.product_id = line.product_id[1]
            line.account_id = line.account_id[1]
            line.uos_id = line.uos_id[1]
            line.note = ns.loads(line.note) if line.note else line.note
            del line.id
            return line

        invoice = ns(self.Invoice.read(cursor, uid, invoice_id, [
            'amount_total',
            'amount_untaxed',
            'partner_id',
            'type',
            'name',
            'number',
            'journal_id',
            'account_id',
            'partner_bank',
            'payment_type',
            'date_invoice',
            'invoice_line',
            'check_total',
            'origin',
            'sii_to_send',
            'mandate_id',
            'state',
        ]))
        invoice.journal_id = invoice.journal_id[1]
        invoice.mandate_id = invoice.mandate_id and invoice.mandate_id[0]
        invoice.partner_bank = invoice.partner_bank[1] if invoice.partner_bank else "None"
        invoice.account_id = invoice.account_id[1]
        invoice.invoice_line = [
            proccesLine(line)
            for line in self.InvoiceLine.read(cursor, uid, invoice.invoice_line, [])
            ]
        self.assertNsEqual(invoice, expected)

    def assertLogEquals(self, log, expected):
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )

        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)

    def assertMailLogEqual(self, log, expected):
        self.assertNsEqual(log or '{}', expected)

    def _generationMailAccount(self, cursor, uid):
        return self.PEAccounts.search(cursor, uid, [
           ('name','=','Generation kWh')
            ])[0]

    def _invertirMailAccount(self, cursor, uid):
        return self.PEAccounts.search(cursor, uid, [
           ('email_id','=','invertir@somenergia.coop')
            ])[0]

    def _aportaMailAccount(self, cursor, uid):
        return self.PEAccounts.search(cursor, uid, [
           ('email_id','=','aporta@somenergia.coop')
            ])[0]

    def _propertyAccountData(self, cursor, uid, demo_id):
        property_account_id = self.IrModelData.get_object_reference(
            cursor, uid, 'som_generationkwh', demo_id
            )[1]
        gkwh_account_value = self.IrProperty.read(cursor, uid, property_account_id, ['value'])['value']
        return self.AccountAccount.read(cursor, uid, int(gkwh_account_value.split(',')[1]), ['name','code'])

    def test_mark_as_signed_allOk_GKWH(self):
        """
        Checks if signed_date change
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, False)

            self.Investment.mark_as_signed(cursor, uid, inv_id, '2017-01-06')

            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, '2017-01-06')

    def test_mark_as_signed_allOk_APO(self):
        """
        Checks if signed_date change
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]

            member_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]

            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, False)

            self.Investment.mark_as_signed(cursor, uid, inv_id, '2017-01-06')

            inv_0001 = self.Investment.read(cursor, uid, inv_id)
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "Aportacions")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': False,
                    'move_line_id': False,
                    'last_effective_date': False,
                    'last_interest_paid_date': False,
                    'nshares': 10,
                    'signed_date': '2017-01-06',
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (member_id, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2020-03-04',
                    'amortized_amount': 0.0,
                    'name': u'APO00001'
                })

    @freeze_time("2020-06-09")
    def test_create_from_form_allOk_APO(self):
        """
        Checks if investment aportacio is created
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2020-06-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'APO_202006')

            member_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]

            inv_0001 = self.Investment.read(cursor, uid, inv_id)
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "Aportacions Juny")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': False,
                    'move_line_id': False,
                    'last_effective_date': False,
                    'last_interest_paid_date': False,
                    'nshares': 40,
                    'signed_date': False,
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (member_id, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2020-06-06',
                    'amortized_amount': 0.0,
                    'name': u'APO000001'
                })
            self.MailMockup.deactivate(cursor, uid)

    @freeze_time("2020-05-09")
    def test_create_from_form_beforeOpenEmission_APO(self):
        """
        Checks if investment aportacio is created
        :return:
        """
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                self.MailMockup.activate(cursor, uid)
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                        partner_id,
                        '2020-06-06',
                        4000,
                        '10.10.23.123',
                        'ES7712341234161234567890',
                        'APO_202006')
                member_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'soci_0001')[1]

                inv_0001 = self.Investment.read(cursor, uid, inv_id)
                inv_0001.pop('actions_log')
                inv_0001.pop('log')
                inv_0001.pop('id')
                id_emission, name_emission = inv_0001.pop('emission_id')
                self.assertEqual(name_emission, "Aportacions Juny")
                self.assertEquals(inv_0001,
                    {
                        'first_effective_date': False,
                        'move_line_id': False,
                        'last_effective_date': False,
                        'last_interest_paid_date': False,
                        'nshares': 40,
                        'signed_date': False,
                        'draft': True,
                        'purchase_date': False,
                        'member_id': (member_id, u'Gil, Pere'),
                        'active': True,
                        'order_date': '2020-06-06',
                        'amortized_amount': 0.0,
                        'name': u'APO000001'
                    })
                self.MailMockup.deactivate(cursor, uid)
        self.assertEqual(str(ctx.exception),'Emission not open yet')

    def test__create_from_form__whenNotAMember_GKWH(self):
        with self.assertRaises(PartnerException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_noinversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )
        self.assertEqual(str(ctx.exception),'Not a member')

    def test__create_from_form__whenNotAMember_APO(self):
        with self.assertRaises(PartnerException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_noinversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(str(ctx.exception),'Not a member')

    def test__create_from_form__withNonDivisibleAmount_APO(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4003,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(str(ctx.exception),'Invalid amount')

    def test__create_from_form__withNonDivisibleAmount_GKWH(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    4003,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )

        self.assertEqual(str(ctx.exception),'Invalid amount')

    def test__create_from_form__withNegativeAmount_APO(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    -400,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(str(ctx.exception),'Invalid amount')

    def test__create_from_form__withNegativeAmount_GKWH(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    -400,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )

        self.assertEqual(str(ctx.exception),'Invalid amount')

    def test__create_from_form__withZeroAmount_APO(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    0,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo',
                    )

        self.assertEqual(str(ctx.exception),'Invalid amount')

    def test__create_from_form__withZeroAmount_GKWH(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    0,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh',
                    )

        self.assertEqual(str(ctx.exception),'Invalid amount')

    def test__create_from_form__withBadIban_APO(self):
        with self.assertRaises(PartnerException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    3000,
                    '10.10.23.123',
                    'ES77123412341612345678ZZ',
                    'emissio_apo',
                    )

        self.assertEqual(str(ctx.exception),'Wrong iban')

    def test__create_from_form__withBadIban_GKWH(self):
        with self.assertRaises(PartnerException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                            )[1]

                inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-01', # order_date
                    3000,
                    '10.10.23.123',
                    'ES77123412341612345678ZZ',
                    'emissio_gkwh',
                    )

        self.assertEqual(str(ctx.exception),'Wrong iban')

    @freeze_time("2020-06-09")
    def test__create_from_form__sendsCreationEmailAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2020-06-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'APO_202006')

            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: generationkwh.investment
                  id: {id}
                  template: aportacio_mail_creacio
                  from_id: [ {account_id} ]
                """.format(
                    id=inv_id,
                    account_id = self._aportaMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__create_from_form__sendsCreationEmailGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2017-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_genkwh')

            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: generationkwh.investment
                  id: {id}
                  template: generationkwh_mail_creacio
                  from_id: [ {account_id} ]
                """.format(
                    id=inv_id,
                    account_id = self._generationMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__create_from_form__ibanIsSet(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_id = self.Investment.create_from_form(cursor, uid,
                partner_id,
                '2017-01-01', # order_date
                2000,
                '10.10.23.1',
                'ES7712341234161234567890',
            )
            partner = self.Partner.browse(cursor, uid, partner_id)
            self.assertTrue(partner.bank_inversions)

    def test__create_initial_invoices__AllOkGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            iban = 'ES7712341234161234567890'
            id = self.Investment.create_from_form(cursor, uid,
                partner_id,
                '2017-01-01', # order_date
                2000,
                '10.10.23.1',
                iban,
                'emissio_genkwh',
                )

            gkwh_account_dict = self._propertyAccountData(cursor, uid, 'property_gkwh_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')

            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            investment = self.Investment.browse(cursor, uid, id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids[0], u"""\
                account_id: {liq_account_code} {liq_account_name}
                amount_total: 2000.0
                amount_untaxed: 2000.0
                check_total: 2000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: {gkwh_account_code} {gkwh_account_name}
                  name: 'Inversió {investment_name} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'CI: {investment_name}-JUST'
                  origin: false
                  price_unit: 100.0
                  price_subtotal: 2000.0
                  note:
                    investmentId: {investment_id}
                    investmentInitialAmount: 2000
                    investmentLastEffectiveDate: false
                    investmentName: GKWH00001
                    investmentPurchaseDate: false
                    pendingCapital: 2000
                  quantity: 20.0
                  product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
                  invoice_line_tax_id: []
                journal_id: Factures GenerationkWh
                mandate_id: {mandate_id}
                name: {investment_name}-JUST
                number: {investment_name}-JUST
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 2
                - Recibo domiciliado
                sii_to_send: false
                type: out_invoice
                state: draft
                """.format(
                invoice_date=datetime.today().strftime("%Y-%m-%d"),
                id=invoice_ids[0],
                iban='ES77 1234 1234 1612 3456 7890',
                year=2018,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=id,
                mandate_id=mandate_id,
                gkwh_account_code=gkwh_account_dict['code'],
                gkwh_account_name=gkwh_account_dict['name'],
                liq_account_code=liq_account_dict['code'],
                liq_account_name=liq_account_dict['name']
                ))

    def test__create_initial_invoices__AllOkAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            apo_account_dict = self._propertyAccountData(cursor, uid, 'property_apo_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')

            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            investment = self.Investment.browse(cursor, uid, id)
            iban = 'ES7712341234161234567890'
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            emission_data = investment.emission_id
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, emission_data.mandate_name, gkwh.creditorCode)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids[0], u"""\
                account_id: {liq_account_code} {liq_account_name}
                amount_total: 1000.0
                amount_untaxed: 1000.0
                check_total: 1000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: {apo_account_code} {apo_account_name}
                  name: 'Inversió {investment_name} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'CI: {investment_name}-JUST'
                  origin: false
                  price_unit: 100.0
                  price_subtotal: 1000.0
                  note:
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: false
                    investmentName: APO00001
                    investmentPurchaseDate: false
                    pendingCapital: 1000
                  quantity: 10.0
                  product_id: '[APO_AE] Aportacions'
                  invoice_line_tax_id: []
                journal_id: Factures Aportacions
                mandate_id: {mandate_id}
                name: {investment_name}-JUST
                number: {investment_name}-JUST
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 2
                - Recibo domiciliado
                sii_to_send: false
                type: out_invoice
                state: draft
                """.format(
                invoice_date=datetime.today().strftime("%Y-%m-%d"),
                id=invoice_ids[0],
                iban='ES77 1234 1234 1612 3456 7890',
                year=2018,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=id,
                mandate_id=mandate_id,
                liq_account_code=liq_account_dict['code'],
                liq_account_name=liq_account_dict['name'],
                apo_account_code=apo_account_dict['code'],
                apo_account_name=apo_account_dict['name']
                ))

    def test__create_initial_invoices__withNegativeAmount_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            investment = self.Investment.browse(cursor, uid, id)
            self.Investment.mark_as_invoiced(cursor, uid, id)

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Investment {name} already invoiced".format(**inv)
                ]))

    def test__create_initial_invoices__withNegativeAmount_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            investment = self.Investment.browse(cursor, uid, id)
            self.Investment.mark_as_invoiced(cursor, uid, id)

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Investment {name} already invoiced".format(**inv)
                ]))

    def test__create_initial_invoices__twice_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            investment = self.Investment.browse(cursor, uid, id)

            self.Investment.create_initial_invoices(cursor, uid, [id])

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Initial Invoice {name}-JUST already exists".format(**inv)
                ]))

    def test__create_initial_invoices__twice_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            investment = self.Investment.browse(cursor, uid, id)

            aa_obj = self.openerp.pool.get('account.account')
            aa_id = aa_obj.search(cursor, uid, [('type','!=','view'),('type','!=','closed')])
            aa_obj.write(cursor, uid, aa_id[0], {'code': '163500000000'})

            self.Investment.create_initial_invoices(cursor, uid, [id])

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Initial Invoice {name}-JUST already exists".format(**inv)
                ]))

    def test__create_initial_invoices__withUnnamedInvestment_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            self.Investment.write(cursor, uid, id, dict(name=None))

            invoice_ids, errs = self.Investment.create_initial_invoices(cursor, uid, [id])

            invoice = self.Invoice.browse(cursor, uid, invoice_ids[0])
            self.assertEqual(invoice.name, "APOID{}-JUST".format(id))

    def test__create_initial_invoices__withUnnamedInvestment_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            self.Investment.write(cursor, uid, id, dict(name=None))

            aa_obj = self.openerp.pool.get('account.account')
            aa_id = aa_obj.search(cursor, uid, [('type','!=','view'),('type','!=','closed')])
            aa_obj.write(cursor, uid, aa_id[0], {'code': '163500000000'})

            invoice_ids, errs = self.Investment.create_initial_invoices(cursor, uid, [id])

            invoice = self.Invoice.browse(cursor, uid, invoice_ids[0])
            self.assertEqual(invoice.name, "GENKWHID{}-JUST".format(id))

    def test__create_initial_invoices__errorWhenNoBank_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            inv = self.Investment.browse(cursor, uid, id)
            self.Partner.write(cursor, uid, inv.member_id.partner_id.id, dict(bank_inversions = False ))

            invoice_ids, errs = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.browse(cursor, uid, id)
            self.assertEqual(errs, [u"""Partner '{name}' has no investment bank account"""
                    .format(name=inv.member_id.partner_id.name)])

    def test__create_initial_invoices__errorWhenNoBank_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            inv = self.Investment.browse(cursor, uid, id)
            self.Partner.write(cursor, uid, inv.member_id.partner_id.id, dict(bank_inversions = False ))

            invoice_ids, errs = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.browse(cursor, uid, id)
            self.assertEqual(errs, [u"""Partner '{name}' has no investment bank account"""
                    .format(name=inv.member_id.partner_id.name)])

    def test__create_initial_invoices__investmentWithPurchaseDate_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            self.Investment.mark_as_invoiced(cursor, uid, id)
            self.Investment.mark_as_paid(cursor, uid, [id], '2016-01-04')

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Investment {name} was already paid".format(**inv)
                ]))

    def test__create_initial_invoices__investmentWithPurchaseDate_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            self.Investment.mark_as_invoiced(cursor, uid, id)
            self.Investment.mark_as_paid(cursor, uid, [id], '2016-01-04')

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Investment {name} was already paid".format(**inv)
                ]))

    def test__create_initial_invoices__inactiveInvestment_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            self.Investment.write(cursor, uid, id, {'active':False})

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Investment {name} is inactive".format(**inv)
                ]))

    def test__create_initial_invoices__inactiveInvestment_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            self.Investment.write(cursor, uid, id, {'active':False})

            result = self.Investment.create_initial_invoices(cursor, uid, [id])

            inv = self.Investment.read(cursor, uid, id)
            self.assertEqual(result, ([], [
                "Investment {name} is inactive".format(**inv)
                ]))

    def test__create_initial_invoices__multiInvestments(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id1 = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            id2 = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]

            aa_obj = self.openerp.pool.get('account.account')
            aa_id = aa_obj.search(cursor, uid, [('type','!=','view'),('type','!=','closed')])
            aa_obj.write(cursor, uid, aa_id[0], {'code': '163000000000'})
            aa_obj.write(cursor, uid, aa_id[1], {'code': '163500000000'})

            result, errs = self.Investment.create_initial_invoices(cursor, uid, [id1,id2])

            self.assertEqual(len(result), 2)

    def test__create_initial_invoices__OkAndKo(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id1 = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            self.Investment.write(cursor, uid, id1, {'active':False})
            id2 = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]

            aa_obj = self.openerp.pool.get('account.account')
            aa_id = aa_obj.search(cursor, uid, [('type','!=','view'),('type','!=','closed')])
            aa_obj.write(cursor, uid, aa_id[0], {'code': '163500000000'})

            result, errs = self.Investment.create_initial_invoices(cursor, uid, [id1,id2])

            inv = self.Investment.read(cursor, uid, id1)
            self.assertEqual(errs, [
                "Investment {name} is inactive".format(**inv),
                ])
            self.assertEqual(len(result), 1)

    def test__create_initial_invoices__twoErrors(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id1 = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            self.Investment.write(cursor, uid, id1, {'active':False})
            id2 = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            self.Investment.mark_as_invoiced(cursor, uid, id2)
            self.Investment.mark_as_paid(cursor, uid, [id2], '2016-01-04')

            result, errs = self.Investment.create_initial_invoices(cursor, uid, [id1,id2])

            inv1 = self.Investment.read(cursor, uid, id1)
            inv2 = self.Investment.read(cursor, uid, id2)
            self.assertEqual(errs, [
                "Investment {name} is inactive".format(**inv1),
                "Investment {name} was already paid".format(**inv2),
                ])
            self.assertEqual(len(result), 0)

    def test__create_initial_invoices__zeroInvestments(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            result, errs = self.Investment.create_initial_invoices(cursor, uid, [])

            self.assertEqual(len(result), 0)

    def test__invoices_to_payment_order_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]

            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])
            self.Investment.open_invoices(cursor, uid, invoice_ids)
            emission_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'emissio_apo'
                        )[1]
            emission_data = self.Emission.browse(cursor, uid, emission_id)

            self.Investment.invoices_to_payment_order(cursor, uid, invoice_ids,
                    emission_data.investment_payment_mode_id.name)

            invoice = self.Invoice.browse(cursor, uid, invoice_ids[0])
            order_id = self.Investment.get_or_create_open_payment_order(cursor,
                    uid, emission_data.investment_payment_mode_id.name)
            lines = self.PaymentLine.search(cursor, uid, [
                ('order_id','=', order_id),
                ('communication','like', invoice.origin),
                ])
            payment_order = self.PaymentOrder.read(cursor, uid, order_id,
                    ['line_ids','create_account_moves','mode','n_lines',
                    'paid', 'payment_type_name','state','total','type'])
            self.assertEquals(payment_order,{
                'create_account_moves': u'bank-statement',
                'line_ids': lines,
                'mode': (emission_data.investment_payment_mode_id.id,
                    emission_data.investment_payment_mode_id.name),
                'n_lines': 1,
                'paid': False,
                'payment_type_name': u'Recibo domiciliado',
                'state': u'draft',
                'total': -1000.0,
                'type': u'receivable',
                'id': payment_order['id'],
             })

    def test__invoices_to_payment_order_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]

            aa_obj = self.openerp.pool.get('account.account')
            aa_id = aa_obj.search(cursor, uid, [('type','!=','view'),('type','!=','closed')])
            aa_obj.write(cursor, uid, aa_id[0], {'code': '163500000000'})

            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])
            self.Investment.open_invoices(cursor, uid, invoice_ids)
            emission_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'emissio_apo'
                        )[1]
            emission_data = self.Emission.browse(cursor, uid, emission_id)

            self.Investment.invoices_to_payment_order(cursor, uid,
                    invoice_ids, emission_data.investment_payment_mode_id.name)

            invoice = self.Invoice.browse(cursor, uid, invoice_ids[0])
            order_id = self.Investment.get_or_create_open_payment_order(cursor,
                    uid, emission_data.investment_payment_mode_id.name)
            lines = self.PaymentLine.search(cursor, uid, [
                ('order_id','=', order_id),
                ('communication','like', invoice.origin),
                ])
            payment_order = self.PaymentOrder.read(cursor, uid, order_id,
                    ['line_ids','create_account_moves','mode','n_lines',
                    'paid', 'payment_type_name','state','total','type'])
            self.assertEquals(payment_order,{
                'create_account_moves': u'bank-statement',
                'line_ids': lines,
                'mode': (emission_data.investment_payment_mode_id.id,
                    emission_data.investment_payment_mode_id.name),
                'n_lines': 1,
                'paid': False,
                'payment_type_name': u'Recibo domiciliado',
                'state': u'draft',
                'total': -1000.0,
                'type': u'receivable',
                'id': payment_order['id'],
            })

    def test__get_or_create_investment_account_APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            investment = self.Investment.browse(cursor, uid, id)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            apo_account_dict = self._propertyAccountData(cursor, uid, 'property_apo_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')


            self.Investment.investment_actions(cursor, uid, investment.id).get_or_create_investment_account(cursor, uid, partner_id)

            partner = self.Partner.browse(cursor, uid, partner_id)
            self.assertEquals(partner.property_account_aportacions.code, apo_account_dict['code'])
            self.assertEquals(partner.property_account_liquidacio.code, liq_account_dict['code'])

    def test__get_or_create_investment_account_GKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            investment = self.Investment.browse(cursor, uid, id)
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            gkwh_account_dict = self._propertyAccountData(cursor, uid, 'property_gkwh_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')

            self.Investment.investment_actions(cursor, uid, investment.id).get_or_create_investment_account(cursor, uid, partner_id)

            partner = self.Partner.browse(cursor, uid, partner_id)
            self.assertEquals(partner.property_account_gkwh.code, gkwh_account_dict['code'])
            self.assertEquals(partner.property_account_liquidacio.code, liq_account_dict['code'])

    def test__amortize__oneAmortizationGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0002'
                        )[1]

            amortization_ids, errors = self.Investment.amortize(cursor, uid, '2021-10-13', [investment_id])

            self.assertEqual(len(amortization_ids), 1)
            self.assertEqual(len(errors), 0)
            invoice = self.Invoice.browse(cursor, uid, amortization_ids[0])
            self.assertEqual(invoice.payment_order_id.mode.name, gkwh.amortizationPaymentMode)
            self.assertEqual(invoice.payment_order_id.mode.tipo, 'sepa34')
            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: account.invoice
                  id: {id}
                  template: generationkwh_mail_amortitzacio
                  from_id: [ {account_id} ]
                """.format(
                    id=amortization_ids[0],
                    account_id = self._generationMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    @mock.patch("som_generationkwh.investment.GenerationkwhInvestment.get_irpf_amounts")
    def test__amortize__negativeAmortizationGKWH(self, get_irpf_mock):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0002'
                        )[1]

            get_irpf_mock.return_value = {'irpf_amount':50}
            amortization_ids, errors = self.Investment.amortize(cursor, uid, '2021-10-13', [investment_id])

            self.assertEqual(len(amortization_ids), 1)
            self.assertEqual(len(errors), 0)
            invoice = self.Invoice.browse(cursor, uid, amortization_ids[0])
            self.assertEqual(invoice.payment_order_id.mode.name, gkwh.amortizationReceivablePaymentMode)
            self.assertEqual(invoice.payment_order_id.mode.tipo, 'sepa19')
            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: account.invoice
                  id: {id}
                  template: generationkwh_mail_amortitzacio
                  from_id: [ {account_id} ]
                """.format(
                    id=amortization_ids[0],
                    account_id = self._generationMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__investment_payment__oneGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            id2 = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]

            aa_obj = self.openerp.pool.get('account.account')
            aa_id = aa_obj.search(cursor, uid, [('type','!=','view'),('type','!=','closed')])
            aa_obj.write(cursor, uid, aa_id[0], {'code': '163500000000'})

            invoice_ids, errors = self.Investment.investment_payment(cursor, uid, [id2])

            self.assertEqual(len(invoice_ids), 1)
            self.assertEqual(len(errors), 0)
            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: account.invoice
                  id: {id}
                  template: generationkwh_mail_pagament
                  from_id: [ {account_id} ]
                """.format(
                    id=invoice_ids[0],
                    account_id = self._generationMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__investment_payment__oneAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            investment = self.Investment.browse(cursor, uid, inv_id)

            invoice_ids, errors = self.Investment.investment_payment(cursor, uid, [inv_id])

            self.assertEqual(len(invoice_ids), 1)
            self.assertEqual(len(errors), 0)
            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: account.invoice
                  id: {id}
                  template: aportacio_mail_pagament
                  from_id: [ {account_id} ]
                """.format(
                    id=invoice_ids[0],
                    account_id = self._aportaMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__get_investments_amount__noInvestments(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_0003'
                        )[1]

            amount = self.Investment.get_investments_amount(cursor, uid,
                member_id,
            )

            self.assertEqual(amount, 0)

    def test__get_investments_amount__moreThanOne_AllEmissions(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_0001'
                        )[1]

            amount = self.Investment.get_investments_amount(cursor, uid,
                member_id,
            )

            self.assertEqual(amount, 6000)

    def test__get_investments_amount__moreThanOne_diferentEmissions(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_0001'
                        )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo'
            )[1]

            amount = self.Investment.get_investments_amount(cursor, uid,
                member_id, emission_id
            )

            self.assertEqual(amount, 1000)

    @freeze_time("2020-06-03")
    def test__get_max_investment__noInvestments_inTemporaLimitWithoutLimitInEmission(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
                    )[1]

            amount = self.Investment.get_max_investment(cursor, uid,
                partner_id, 'APO_202006'
            )
            #emission limit date is

            self.assertEqual(amount, 100000)

    @freeze_time("2020-06-13")
    def test__get_max_investment__noInvestments_outOfTemporaLimitWithoutLimitInEmission(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
                    )[1]

            amount = self.Investment.get_max_investment(cursor, uid,
                partner_id, 'APO_202006'
            )

            self.assertEqual(amount, 100000)

    @freeze_time("2020-06-03")
    def test__get_max_investment__noInvestments_inTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo2'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 5000,
                                 'limited_period_end_date': '2020-06-10',
                                 'current_total_amount_invested': 0})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202006'
                                                        )
            self.assertEqual(amount, 5000)

    @freeze_time("2020-06-13")
    def test__get_max_investment__noInvestments_outOfTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo2'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 5000,
                                 'limited_period_end_date': '2020-06-10',
                                 'current_total_amount_invested': 0})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202006'
                                                        )

            self.assertEqual(amount, 100000)

    @freeze_time("2020-06-03")
    def test__get_max_investment__withInvestments_inTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo2'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 1000,
                                 'limited_period_end_date': '2020-06-10'})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202006'
                                                        )
            self.assertEqual(amount, 0)

    @freeze_time("2020-06-11")
    def test__get_max_investment__withInvestments_overEmissionLimit(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                )[1]
                emission_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'emissio_apo2'
                )[1]
                self.Emission.write(cursor, uid, emission_id,
                                    {'limited_period_amount': 1000,
                                     'amount_emission': 4900,
                                     'limited_period_end_date': '2020-06-10'})

                amount = self.Investment.get_max_investment(cursor, uid,
                                                            partner_id, 'APO_202006'
                                                            )

        self.assertEqual(str(ctx.exception),'Emission completed')

    @freeze_time("2020-06-13")
    def test__get_max_investment__withInvestments_outOfTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo2'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 1000,
                                 'limited_period_end_date': '2020-06-10'})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202006'
                                                        )

            self.assertEqual(amount, 94000)

    @freeze_time("2020-06-03")
    def test__get_max_investment__withOldInvestments_inTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor2'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo2'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 1000,
                                 'limited_period_end_date': '2020-06-10'})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202006'
                                                        )
            self.assertEqual(amount, 1000)

    @freeze_time("2020-03-13")
    def test__get_max_investment__emissionNotExist(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor2'
                            )[1]
                emission_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'emissio_apo'
                )[1]

                amount = self.Investment.get_max_investment(cursor, uid,
                                                            partner_id, 'fake_emission_code'
                                                            )

        self.assertEqual(str(ctx.exception),'Emission closed or not exist')

    @freeze_time("2020-06-01")
    def test__get_max_investment__emissionDayBeforeOpen(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor2'
                            )[1]
                emission_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'emissio_apo2'
                )[1]
                self.Emission.write(cursor, uid, emission_id,
                                {'start_date': '2020-06-03', })

                amount = self.Investment.get_max_investment(cursor, uid,
                                                            partner_id, 'APO_202006'
                                                            )

        self.assertEqual(str(ctx.exception),'Emission not open yet')

    @freeze_time("2020-09-01")
    def test__get_max_investment__emissionDayAfterClosed(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor2'
                            )[1]
                emission_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'emissio_apo2'
                )[1]
                self.Emission.write(cursor, uid, emission_id,
                                {'end_date': '2020-08-30', })

                amount = self.Investment.get_max_investment(cursor, uid,
                                                            partner_id, 'APO_202006'
                                                            )

        self.assertEqual(str(ctx.exception),'Emission closed')

    @freeze_time("2020-03-04")
    def test__get_max_investment__emissionNotOpen(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                partner_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'res_partner_inversor2'
                            )[1]
                emission_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'emissio_apo'
                )[1]
                self.Emission.write(cursor, uid, emission_id,
                                {'state': 'draft', })

                amount = self.Investment.get_max_investment(cursor, uid,
                                                            partner_id, 'APO_202003'
                                                            )

        self.assertEqual(str(ctx.exception),'Emission closed or not exist')

    def test_mark_as_paid__allOk_APO(self):
        """
        Checks if signed_date change
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]

            member_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]

            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.Investment.mark_as_invoiced(cursor, uid, inv_id)

            self.Investment.mark_as_paid(cursor, uid, [inv_id], '2017-01-06')

            inv_0001 = self.Investment.read(cursor, uid, inv_id)
            self.assertLogEquals(inv_0001['log'],
                u'PAID: Pagament de 1000 € efectuat [None]\n'
                u'INVOICED: Facturada i remesada\n'
            )
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "Aportacions")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': '2017-01-06',
                    'move_line_id': False,
                    'last_effective_date': False,
                    'last_interest_paid_date': False,
                    'nshares': 10,
                    'signed_date': False,
                    'draft': False,
                    'purchase_date': '2017-01-06',
                    'member_id': (member_id, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2020-03-04',
                    'amortized_amount': 0.0,
                    'name': u'APO00001'
                })

    def test_mark_as_paid__allOk_GKWH(self):
        """
        Checks if signed_date change
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]

            member_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]

            inv_0001 = self.Investment.browse(cursor, uid, inv_id)
            self.Investment.mark_as_invoiced(cursor, uid, inv_id)

            self.Investment.mark_as_paid(cursor, uid, [inv_id], '2017-01-06')

            inv_0001 = self.Investment.read(cursor, uid, inv_id)
            self.assertLogEquals(inv_0001['log'],
                u'PAID: Pagament de 1000 € efectuat [None]\n'
                u'INVOICED: Facturada i remesada\n'
            )
            inv_0001.pop('actions_log')
            inv_0001.pop('log')
            inv_0001.pop('id')
            id_emission, name_emission = inv_0001.pop('emission_id')
            self.assertEqual(name_emission, "GenerationkWH")
            self.assertEquals(inv_0001,
                {
                    'first_effective_date': '2018-01-06',
                    'move_line_id': False,
                    'last_effective_date': '2042-01-06',
                    'last_interest_paid_date': False,
                    'nshares': 10,
                    'signed_date': False,
                    'draft': False,
                    'purchase_date': '2017-01-06',
                    'member_id': (member_id, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2019-10-01',
                    'amortized_amount': 0.0,
                    'name': u'GKWH00001'
                })

    def test__effective_investments_tuple__allGKWH(self):
        """
        Check effective investments tuple, only Generation
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            member1_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]

            member2_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_generation')[1]

            inv_tuple = self.Investment.effective_investments_tuple(cursor, uid)

            self.assertEquals(inv_tuple, [
                (member1_id, False, False, 10),
                (member1_id, '2020-10-12', '2044-10-12', 10),
                (member2_id, '2020-11-12', '2044-11-12', 5),
            ])

    def test__effective_investments_tuple__allAPO(self):
        """
        Check effective investments tuple, only Generation
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            member1_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]

            member2_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_aportacions')[1]

            inv_tuple = self.Investment.effective_investments_tuple(cursor, uid, emission_type='apo')

            self.assertEquals(set(inv_tuple), set([
                (member1_id, False, False, 50),
                (member1_id, False, False, 10),
                (member2_id, '2020-03-12', False, 10),
            ]))

    def test__effective_investments_tuple__filteredByEmissionCode(self):
        """
        Check effective investments tuple, only Generation
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]

            member_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]

            inv_tuple = self.Investment.effective_investments_tuple(cursor, uid, emission_type='apo', emission_code='APO_202006')

            self.assertEquals(inv_tuple, [(member_id, False, False, 50)])

    def test__member_has_effective__onlyGKWH(self):
        """
        Check if member has Generation
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_generation'
                        )[1]

            has_effectives = self.Investment.member_has_effective(cursor, uid, member_id, '2010-01-01','2022-01-01')

            self.assertTrue(has_effectives)

    def test__member_has_effective__onlyAPO(self):
        """
        Check if member has Generation
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_aportacions'
                        )[1]

            has_effectives = self.Investment.member_has_effective(cursor, uid, member_id, '2010-01-01','2022-01-01', emission_type='apo')

            self.assertTrue(has_effectives)

    def test__member_has_effective__noGKWH(self):
        """
        Check if member has Generation
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_aportacions'
                        )[1]

            has_effectives = self.Investment.member_has_effective(cursor, uid, member_id, '2010-01-01','2022-01-01')

            self.assertFalse(has_effectives)

    def test__member_has_effective__noAPO(self):
        """
        Check if member has Generation
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_generation'
                        )[1]

            has_effectives = self.Investment.member_has_effective(cursor, uid, member_id, '2010-01-01','2022-01-01', emission_type='apo')

            self.assertFalse(has_effectives)

    def test__pending_amortization_summary__manyAmortizationsSameInvestment(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0002'
                        )[1]

            self.assertEqual((2, 80),
                self.Investment.pending_amortization_summary(cursor, uid, '2022-11-20', [inv_id]))

    def test__pending_amortization_summary__allInvestments(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.assertEqual((4, 120),
                self.Investment.pending_amortization_summary(cursor, uid, '2022-11-20'))

    def test__get_stats_investment_generation__when_last_effective_date(self):
        """
        Check get_stats_investment_generation when some investements with last_effective_date
        """

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            inv_ids = self.Investment.search(cursor, uid, [('emission_id.type', '=', 'genkwh')])

            with_last_effective_date = len(inv_ids) / 2 if inv_ids else 0

            with_last_effective_date_ids = inv_ids[:with_last_effective_date]
            without_last_effective_date_ids = inv_ids[with_last_effective_date:]

            inv_datas = self.Investment.read(cursor, uid, without_last_effective_date_ids, ['member_id'])
            members = [inv_data['member_id'] for inv_data in inv_datas]

            today = date.today().strftime('%Y-%m-%d')
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

            self.Investment.write(cursor, uid, without_last_effective_date_ids ,{'last_effective_date':None})
            self.Investment.write(cursor, uid, with_last_effective_date_ids ,{'last_effective_date': yesterday})

            ret = self.Investment.get_stats_investment_generation(cursor, uid, {'today': today})
            socis = ret[0]['socis']

            self.assertEqual(socis, len(set(members)))

    def test__get_stats_investment_generation__when_last_effective_date_not_done(self):
        """
        Check get_stats_investment_generation when some investements with last_effective_date not done
        """

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            inv_ids = self.Investment.search(cursor, uid, [('emission_id.type', '=', 'genkwh')])
            inv_datas = self.Investment.read(cursor, uid, inv_ids, ['member_id'])
            members = [inv_data['member_id'] for inv_data in inv_datas]

            with_last_effective_date = len(inv_ids) / 2 if inv_ids else 0

            with_last_effective_date_ids = inv_ids[:with_last_effective_date]
            without_last_effective_date_ids = inv_ids[with_last_effective_date:]

            today = date.today().strftime('%Y-%m-%d')
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

            self.Investment.write(cursor, uid, without_last_effective_date_ids ,{'last_effective_date':None})
            self.Investment.write(cursor, uid, with_last_effective_date_ids ,{'last_effective_date': today})

            ret = self.Investment.get_stats_investment_generation(cursor, uid, {'today': yesterday})
            socis = ret[0]['socis']

            self.assertEqual(socis, len(set(members)))

    def test__get_stats_investment_generation__amount_when_last_effective_date(self):
        """
        Check get_stats_investment_generation when some investements with last_effective_date
        """

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            inv_ids = self.Investment.search(cursor, uid, [('emission_id.type', '=', 'genkwh')])

            with_last_effective_date = len(inv_ids) / 2 if inv_ids else 0

            with_last_effective_date_ids = inv_ids[:with_last_effective_date]
            without_last_effective_date_ids = inv_ids[with_last_effective_date:]

            today = date.today().strftime('%Y-%m-%d')
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

            self.Investment.write(cursor, uid, without_last_effective_date_ids ,{'last_effective_date':None , 'nshares':10})
            self.Investment.write(cursor, uid, with_last_effective_date_ids ,{'last_effective_date':yesterday})

            ret = self.Investment.get_stats_investment_generation(cursor, uid, {'today': today})
            amount = ret[0]['amount']

            self.assertEqual(amount, len(without_last_effective_date_ids) * 1000)

    def test__get_stats_investment_generation__amount_when_last_effective_date_not_done(self):
        """
        Check get_stats_investment_generation when some investements with last_effective_date not done
        """

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            inv_ids = self.Investment.search(cursor, uid, [('emission_id.type', '=', 'genkwh')])

            with_last_effective_date = len(inv_ids) / 2 if inv_ids else 0

            with_last_effective_date_ids = inv_ids[:with_last_effective_date]
            without_last_effective_date_ids = inv_ids[with_last_effective_date:]

            today = date.today().strftime('%Y-%m-%d')
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

            self.Investment.write(cursor, uid, without_last_effective_date_ids ,{'last_effective_date':None , 'nshares':10})
            self.Investment.write(cursor, uid, with_last_effective_date_ids ,{'last_effective_date':today , 'nshares':10})

            ret = self.Investment.get_stats_investment_generation(cursor, uid, {'today': yesterday})
            amount = ret[0]['amount']

            self.assertEqual(amount, len(inv_ids) * 1000)


    def test__get_stats_investment_generation__amount_2023(self):
        """
        Check get_stats_investment_generation temporally amount_2023 field
        """

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            inv_ids = self.Investment.search(cursor, uid, [('emission_id.type', '=', 'genkwh')])
            self.Investment.write(cursor, uid, inv_ids[-1] , {'order_date': date(2023, 9, 27) , 'nshares': 5})

            ret = self.Investment.get_stats_investment_generation(cursor, uid)
            amount_2023 = ret[0]['amount_2023']

            self.assertEqual(amount_2023, 500)


    def test__create_divestment_invoice__withouProfitGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            iban = 'ES7712341234161234567890'
            investment = self.Investment.browse(cursor, uid, investment_id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            date_invoice = '2020-04-23'
            pending_amount = 1000
            gkwh_account_dict = self._propertyAccountData(cursor, uid, 'property_gkwh_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')

            invoice_ids, errs =  self.Investment.create_divestment_invoice(cursor, uid, investment_id, date_invoice, pending_amount)

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids, u"""\
                account_id: {liq_account_code} {liq_account_name}
                amount_total: 1000.0
                amount_untaxed: 1000.0
                check_total: 1000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: {gkwh_account_code} {gkwh_account_name}
                  name: 'Desinversió total de {investment_name} a {invoice_date} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  origin: false
                  price_unit: 1000.0
                  price_subtotal: 1000.0
                  note:
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: false
                    investmentName: GKWH00001
                    investmentPurchaseDate: false
                    divestmentDate: '{invoice_date}'
                    pendingCapital: 0.0
                  quantity: 1.0
                  product_id: '[GENKWH_AMOR] Amortització Generation kWh'
                  invoice_line_tax_id: []
                journal_id: Amortització GenerationkWh
                mandate_id: {mandate_id}
                name: {investment_name}-DES
                number: {investment_name}-DES
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 3
                - Transferencia
                sii_to_send: false
                type: in_invoice
                state: draft
                """.format(
                invoice_date='2020-04-23',
                id=invoice_ids,
                iban='ES77 1234 1234 1612 3456 7890',
                year=2018,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=investment_id,
                mandate_id=mandate_id,
                gkwh_account_code=gkwh_account_dict['code'],
                gkwh_account_name=gkwh_account_dict['name'],
                liq_account_code=liq_account_dict['code'],
                liq_account_name=liq_account_dict['name']
                ))

    def test__create_divestment_invoice__withProfitOneYearOkGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            iban = 'ES7712341234161234567890'
            investment = self.Investment.browse(cursor, uid, investment_id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            date_invoice = '2020-04-23'
            pending_amount = 1000
            irpf_amount_current_year = 7
            irpf_amount = 0

            gkwh_account_dict = self._propertyAccountData(cursor, uid, 'property_gkwh_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')

            invoice_ids, errs =  self.Investment.create_divestment_invoice(cursor, uid, investment_id, date_invoice, pending_amount, irpf_amount_current_year, irpf_amount)

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids, u"""\
                account_id: {liq_account_code} {liq_account_name}
                amount_total: 993.0
                amount_untaxed: 993.0
                check_total: 993.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: {gkwh_account_code} {gkwh_account_name}
                  name: 'Desinversió total de {investment_name} a {invoice_date} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  origin: false
                  price_unit: 1000.0
                  price_subtotal: 1000.0
                  note:
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: false
                    investmentName: GKWH00001
                    investmentPurchaseDate: false
                    divestmentDate: '{invoice_date}'
                    pendingCapital: 0.0
                  quantity: 1.0
                  product_id: '[GENKWH_AMOR] Amortització Generation kWh'
                  invoice_line_tax_id: []
                - account_analytic_id: false
                  account_id: 475119000001 IRPF 19% GENERATION KWh
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  invoice_line_tax_id: []
                  name: 'Retenció IRPF sobre l''estalvi del Generationkwh de {year} de {investment_name} '
                  note:
                    divestmentDate: '{invoice_date}'
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: {last_effective_date}
                    investmentName: {investment_name}
                    investmentPurchaseDate: {purchase_date}
                    pendingCapital: 0.0
                  origin: false
                  price_subtotal: -7.0
                  price_unit: -7.0
                  product_id: '[GENKWH_IRPF] Retenció IRPF estalvi Generation kWh'
                  quantity: 1.0
                  uos_id: PCE
                journal_id: Amortització GenerationkWh
                mandate_id: {mandate_id}
                name: {investment_name}-DES
                number: {investment_name}-DES
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 3
                - Transferencia
                sii_to_send: false
                type: in_invoice
                state: draft
                """.format(
                invoice_date='2020-04-23',
                id=invoice_ids,
                iban='ES77 1234 1234 1612 3456 7890',
                year=2020,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=investment_id,
                mandate_id=mandate_id,
                purchase_date=investment.purchase_date,
                last_effective_date=investment.last_effective_date,
                gkwh_account_code=gkwh_account_dict['code'],
                gkwh_account_name=gkwh_account_dict['name'],
                liq_account_code=liq_account_dict['code'],
                liq_account_name=liq_account_dict['name']
                ))

    def test__create_divestment_invoice__withProfitTwoYears_irpNotRoundedOkGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            iban = 'ES7712341234161234567890'
            investment = self.Investment.browse(cursor, uid, investment_id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            date_invoice = '2020-04-23'
            pending_amount = 1000
            irpf_amount_current_year = 0.032211777
            irpf_amount = 0.073257954
            gkwh_account_dict = self._propertyAccountData(cursor, uid, 'property_gkwh_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')

            invoice_ids, errs =  self.Investment.create_divestment_invoice(cursor, uid, investment_id, date_invoice, pending_amount, irpf_amount_current_year, irpf_amount)

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids, u"""\
                account_id: {liq_account_code} {liq_account_name}
                amount_total: 999.9
                amount_untaxed: 999.9
                check_total: 999.9
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: {gkwh_account_code} {gkwh_account_name}
                  name: 'Desinversió total de {investment_name} a {invoice_date} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  origin: false
                  price_unit: 1000.0
                  price_subtotal: 1000.0
                  note:
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: false
                    investmentName: GKWH00001
                    investmentPurchaseDate: false
                    divestmentDate: '{invoice_date}'
                    pendingCapital: 0.0
                  quantity: 1.0
                  product_id: '[GENKWH_AMOR] Amortització Generation kWh'
                  invoice_line_tax_id: []
                - account_analytic_id: false
                  account_id: 475119000001 IRPF 19% GENERATION KWh
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  invoice_line_tax_id: []
                  name: 'Retenció IRPF sobre l''estalvi del Generationkwh de {year} de {investment_name} '
                  note:
                    divestmentDate: '{invoice_date}'
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: {last_effective_date}
                    investmentName: {investment_name}
                    investmentPurchaseDate: {purchase_date}
                    pendingCapital: 0.0
                  origin: false
                  price_subtotal: -0.03
                  price_unit: -0.03
                  product_id: '[GENKWH_IRPF] Retenció IRPF estalvi Generation kWh'
                  quantity: 1.0
                  uos_id: PCE
                - account_analytic_id: false
                  account_id: 475119000001 IRPF 19% GENERATION KWh
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  invoice_line_tax_id: []
                  name: 'Retenció IRPF sobre l''estalvi del Generationkwh de {yearm1} de {investment_name} '
                  note:
                    divestmentDate: '{invoice_date}'
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: {last_effective_date}
                    investmentName: {investment_name}
                    investmentPurchaseDate: {purchase_date}
                    pendingCapital: 0.0
                  origin: false
                  price_subtotal: -0.07
                  price_unit: -0.07
                  product_id: '[GENKWH_IRPF] Retenció IRPF estalvi Generation kWh'
                  quantity: 1.0
                  uos_id: PCE
                journal_id: Amortització GenerationkWh
                mandate_id: {mandate_id}
                name: {investment_name}-DES
                number: {investment_name}-DES
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 3
                - Transferencia
                sii_to_send: false
                type: in_invoice
                state: draft
                """.format(
                invoice_date='2020-04-23',
                id=invoice_ids,
                iban='ES77 1234 1234 1612 3456 7890',
                year=2020,
                yearm1 = 2019,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=investment_id,
                mandate_id=mandate_id,
                purchase_date=investment.purchase_date,
                last_effective_date=investment.last_effective_date,
                gkwh_account_code=gkwh_account_dict['code'],
                gkwh_account_name=gkwh_account_dict['name'],
                liq_account_code=liq_account_dict['code'],
                liq_account_name=liq_account_dict['name']
                ))



    def test__create_divestment_invoice__withProfitTwoYears_okGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]

            gkwh_account_dict = self._propertyAccountData(cursor, uid, 'property_gkwh_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')
            iban = 'ES7712341234161234567890'
            investment = self.Investment.browse(cursor, uid, investment_id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            date_invoice = '2020-04-23'
            pending_amount = 1000
            irpf_amount_current_year = 7
            irpf_amount = 3

            invoice_ids, errs =  self.Investment.create_divestment_invoice(cursor, uid, investment_id, date_invoice, pending_amount, irpf_amount_current_year, irpf_amount)

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids, u"""\
                account_id: {liq_account_code} {liq_account_name}
                amount_total: 990.0
                amount_untaxed: 990.0
                check_total: 990.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: {gkwh_account_code} {gkwh_account_name}
                  name: 'Desinversió total de {investment_name} a {invoice_date} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  origin: false
                  price_unit: 1000.0
                  price_subtotal: 1000.0
                  note:
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: false
                    investmentName: GKWH00001
                    investmentPurchaseDate: false
                    divestmentDate: '{invoice_date}'
                    pendingCapital: 0.0
                  quantity: 1.0
                  product_id: '[GENKWH_AMOR] Amortització Generation kWh'
                  invoice_line_tax_id: []
                - account_analytic_id: false
                  account_id: 475119000001 IRPF 19% GENERATION KWh
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  invoice_line_tax_id: []
                  name: 'Retenció IRPF sobre l''estalvi del Generationkwh de {year} de {investment_name} '
                  note:
                    divestmentDate: '{invoice_date}'
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: {last_effective_date}
                    investmentName: {investment_name}
                    investmentPurchaseDate: {purchase_date}
                    pendingCapital: 0.0
                  origin: false
                  price_subtotal: -7.0
                  price_unit: -7.0
                  product_id: '[GENKWH_IRPF] Retenció IRPF estalvi Generation kWh'
                  quantity: 1.0
                  uos_id: PCE
                - account_analytic_id: false
                  account_id: 475119000001 IRPF 19% GENERATION KWh
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  invoice_line_tax_id: []
                  name: 'Retenció IRPF sobre l''estalvi del Generationkwh de {yearm1} de {investment_name} '
                  note:
                    divestmentDate: '{invoice_date}'
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: {last_effective_date}
                    investmentName: {investment_name}
                    investmentPurchaseDate: {purchase_date}
                    pendingCapital: 0.0
                  origin: false
                  price_subtotal: -3.0
                  price_unit: -3.0
                  product_id: '[GENKWH_IRPF] Retenció IRPF estalvi Generation kWh'
                  quantity: 1.0
                  uos_id: PCE
                journal_id: Amortització GenerationkWh
                mandate_id: {mandate_id}
                name: {investment_name}-DES
                number: {investment_name}-DES
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 3
                - Transferencia
                sii_to_send: false
                type: in_invoice
                state: draft
                """.format(
                invoice_date='2020-04-23',
                id=invoice_ids,
                iban='ES77 1234 1234 1612 3456 7890',
                year=2020,
                yearm1 = 2019,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=investment_id,
                mandate_id=mandate_id,
                purchase_date=investment.purchase_date,
                last_effective_date=investment.last_effective_date,
                gkwh_account_code=gkwh_account_dict['code'],
                gkwh_account_name=gkwh_account_dict['name'],
                liq_account_code=liq_account_dict['code'],
                liq_account_name=liq_account_dict['name']
                ))

    def test__create_divestment_invoice__APO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            iban = 'ES7712341234161234567890'

            investment = self.Investment.browse(cursor, uid, investment_id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            date_invoice = '2020-04-23'
            pending_amount = 1000
            apo_account_dict = self._propertyAccountData(cursor, uid, 'property_apo_account_demo')
            liq_account_dict = self._propertyAccountData(cursor, uid, 'property_liq_account_demo')

            invoice_ids, errs = self.Investment.create_divestment_invoice(cursor, uid, investment_id, date_invoice, pending_amount)

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids, u"""\
                account_id: {liq_account_code} {liq_account_name}
                amount_total: 1000.0
                amount_untaxed: 1000.0
                check_total: 1000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: {apo_account_code} {apo_account_name}
                  name: 'Desinversió total de {investment_name} a {invoice_date} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  origin: false
                  price_unit: 1000.0
                  price_subtotal: 1000.0
                  note:
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: false
                    investmentName: APO00001
                    investmentPurchaseDate: false
                    divestmentDate: '{invoice_date}'
                    pendingCapital: 0.0
                  quantity: 1.0
                  product_id: '[APO_AE] Aportacions'
                  invoice_line_tax_id: []
                journal_id: Factures Liquidació Aportacions
                mandate_id: {mandate_id}
                name: {investment_name}-DES
                number: {investment_name}-DES
                origin: {investment_name}
                partner_bank: {iban}
                partner_id:
                - {p.id}
                - {p.name}
                payment_type:
                - 3
                - Transferencia
                sii_to_send: false
                type: in_invoice
                state: draft
                """.format(
                invoice_date='2020-04-23',
                id=invoice_ids,
                iban='ES77 1234 1234 1612 3456 7890',
                year=2018,
                investment_name=investment.name,
                p=partner_data,
                num_soci=partner_data.ref[1:],
                investment_id=investment_id,
                mandate_id=mandate_id,
                apo_account_name=apo_account_dict['name'],
                apo_account_code=apo_account_dict['code'],
                liq_account_code=liq_account_dict['code'],
                liq_account_name=liq_account_dict['name']
                ))

    def test__divest_investment__APO_whenOne(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            investment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'apo_0003'
            )[1]
            member_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001'
            )[1]

            self.Investment.write(cursor, uid, investment_id, {'member_id': member_id})

            self.Investment.divest(cursor, uid, [investment_id])

            last_effective_date = self.Investment.read(cursor, uid, investment_id, ['last_effective_date'])['last_effective_date']
            today = datetime.today().strftime("%Y-%m-%d")

            self.assertEqual(last_effective_date, today)

            #2019-10-01
    def test__divest_investment__GkWh_withOutProfit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            investment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'genkwh_0002'
            )[1]

            aa_obj = self.openerp.pool.get('account.account')
            aa_id = aa_obj.search(cursor, uid, [('type','!=','view'),('type','!=','closed')])
            aa_obj.write(cursor, uid, aa_id[0], {'code': '163500000000'})

            self.Investment.divest(cursor, uid, [investment_id])

            last_effective_date = self.Investment.read(cursor, uid, investment_id, ['last_effective_date'])['last_effective_date']
            today = datetime.today().strftime("%Y-%m-%d")
            self.assertEqual(last_effective_date, today)

    @mock.patch("giscedata_signatura_documents_signaturit.giscedata_signatura_documents.GiscedataSignaturaProcess.start")
    def test__generationwkwh_investment_sign__ok(self, mocked_sign):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            investment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'genkwh_0002'
            )[1]

            self.Investment.investment_sign_request(cursor, uid, investment_id)
            mocked_sign.assert_called_with(cursor, uid, mock.ANY, context={})

    @unittest.skip("No implemented yet. Keep in mind to mock ResPartnerAddress.write()")
    def test__generationwkwh_investment_sign__withoutMail(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            investment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'genkwh_0002'
            )[1]
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            address_id = self.PartnerAddress.search(cursor, uid, [('partner_id', '=', partner_id)])[0]
            self.PartnerAddress.write(cursor, uid, [address_id], {'email': False})

            with self.assertRaises(except_osv) as ctx:
                self.Investment.investment_sign_request(cursor, uid, investment_id)

    def test__generationwkwh_investment_sign__withoutInvoice(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            investment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'genkwh_0001'
            )[1]

            with self.assertRaises(except_osv) as ctx:
                self.Investment.investment_sign_request(cursor, uid, investment_id)

            
    @unittest.skip("No implemented yet. Keep in mind to mock ResPartnerAddress.write()")
    def test__generationwkwh_investment_sign_callback__ok(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            investment_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'genkwh_0002'
            )[1]
            self.Investment.write(cursor, uid, investment_id, {'signed_date': False})
            self.Investment.investment_sign_request(cursor, uid, investment_id)
            context = {
                'process_data': {
                    'callback_method': 'generationkwh_signed',
                    'gen_id': investment_id
                }
            }
            self.Invoice.process_signature_callback(cursor, uid, [], context)
            signed_date = self.Investment.read(cursor, uid, investment_id, ['signed_date'])['signed_date']
            self.assertTrue(signed_date)


    def test__has_interest_invoice__False(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]

            inv_id = self.Investment.has_interest_invoice(cursor, uid, investment_id)

            self.assertFalse(inv_id)
            self.MailMockup.deactivate(cursor, uid)

    def test__has_interest_invoice__True(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]

            inv_id = self.Investment.has_interest_invoice(cursor, uid, investment_id, 2020)

            self.assertTrue(inv_id)
            self.MailMockup.deactivate(cursor, uid)

    def test__interest__oneInvoiceAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]

            context = {'open_invoices': True}
            vals = {
                'date_invoice': '2021-06-30',
                'date_start': '2020-06-30',
                'date_end': '2021-06-30',
                'to_be_interized': 8.1,
                'interest_rate': 1.0
            }
            interest_ids, errors = self.Investment.interest(cursor, uid, [investment_id], vals, context)

            self.assertEqual(len(interest_ids), 1)
            self.assertEqual(len(errors), 0)
            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: account.invoice
                  id: {id}
                  template: aportacio_interest_notification_mail
                  from_id: [ {account_id} ]
                """.format(
                    id=interest_ids[0],
                    account_id=self._aportaMailAccount(cursor, uid),
                ))
            self.MailMockup.deactivate(cursor, uid)

    def test__interest__tryTwoInterestOnlyOneDone(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]
            vals = {
                'date_invoice': '2021-06-30',
                'date_start': '2020-06-30',
                'date_end': '2021-06-30',
                'to_be_interized': 8.1,
                'interest_rate': 1.0
            }
            interest_ids, errors = self.Investment.interest(cursor, uid, [investment_id], vals)
            interest_ids2, errors2 = self.Investment.interest(cursor, uid, [investment_id], vals)

            self.assertEqual(len(interest_ids), 1)
            self.assertEqual(len(errors), 0)
            self.assertEqual(len(interest_ids2), 0)
            self.MailMockup.deactivate(cursor, uid)

    def test__interest__notCreatedGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0002'
                        )[1]
            vals = {
                'date_invoice': '2021-06-30',
                'date_start': '2020-06-30',
                'date_end': '2021-06-30',
                'to_be_interized': 8.1,
                'interest_rate': 1.0
            }

            interest_ids, errors = self.Investment.interest(cursor, uid, [investment_id], vals)

            self.assertEqual(len(interest_ids), 0)
            self.assertEqual(len(errors), 1)
            self.MailMockup.deactivate(cursor, uid)

    def test__interest__notPayed(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]
            vals = {
                'date_invoice': '2021-06-30',
                'date_start': '2020-06-30',
                'date_end': '2021-06-30',
                'to_be_interized': 8.1,
                'interest_rate': 1.0
            }
            interest_ids, errors = self.Investment.interest(cursor, uid, [investment_id], vals)

            self.assertEqual(len(interest_ids), 0)
            self.assertEqual(len(errors), 1)
            self.MailMockup.deactivate(cursor, uid)

    def test__get_to_be_interized__NotPayed(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                product_id = self.Product.search(cursor, uid, [
                    ('default_code','=', 'APO_INT'),
                ])[0]
                inv_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'apo_0001'
                            )[1]
                inv_obj = self.Investment.browse(cursor, uid, inv_id)
                current_interest = self.Emission.current_interest(cursor, uid)
                vals = {
                    'date_invoice': '2021-06-30',
                    'date_start': '2020-06-30',
                    'date_end': '2021-06-30',
                    'interest_rate': current_interest
                }

                amount = self.Investment.get_to_be_interized(cursor, uid, inv_id, vals)

    def test__get_to_be_interized__AllYear_leapYear(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]
            current_interest = self.Emission.current_interest(cursor, uid)
            vals = {
                'date_invoice': '2021-06-30',
                'date_start': '2020-07-01',
                'date_end': '2021-06-30',
                'interest_rate': current_interest
            }

            to_be_interized = self.Investment.get_to_be_interized(cursor, uid, inv_id, vals, {})

            self.assertEqual(to_be_interized, 9.99)

    def test__get_to_be_interized__AllYear_notLeapYear(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]
            current_interest = self.Emission.current_interest(cursor, uid)
            vals = {
                'date_invoice': '2022-06-30',
                'date_start': '2021-07-01',
                'date_end': '2022-06-30',
                'interest_rate': current_interest
            }

            to_be_interized = self.Investment.get_to_be_interized(cursor, uid, inv_id, vals, {})

            self.assertEqual(to_be_interized, 10)

    def test__get_to_be_interized__NotInterestAndDivested(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                inv_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'apo_0003'
                            )[1]
                self.Investment.write(cursor, uid, inv_id, {'last_effective_date' : '2020-06-23'})
                current_interest = self.Emission.current_interest(cursor, uid)
                vals = {
                    'date_invoice': '2021-06-30',
                    'date_start': '2020-06-30',
                    'date_end': '2021-06-30',
                    'interest_rate': current_interest
                }

                self.Investment.get_to_be_interized(cursor, uid, inv_id, vals, {})

    def test__get_to_be_interized__InterestAndDivested_notLeap(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]
            inv_obj = self.Investment.browse(cursor, uid, inv_id)
            inv_obj.write({'last_effective_date' : '2020-12-31'})
            current_interest = self.Emission.current_interest(cursor, uid)
            vals = {
                'date_invoice': '2021-06-30',
                'date_start': '2020-07-01',
                'date_end': '2021-06-30',
                'interest_rate': current_interest
            }
            amount = self.Investment.get_to_be_interized(cursor, uid, inv_id, vals, {})

            self.assertEqual(amount, 5.03)

    def test__get_to_be_interized__InterestAndDivested_leapYear(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]
            inv_obj = self.Investment.browse(cursor, uid, inv_id)
            inv_obj.write({'last_effective_date' : '2021-12-31'})
            current_interest = self.Emission.current_interest(cursor, uid)
            vals = {
                'date_invoice': '2022-06-30',
                'date_start': '2021-07-01',
                'date_end': '2022-06-30',
                'interest_rate': current_interest
            }
            amount = self.Investment.get_to_be_interized(cursor, uid, inv_id, vals, {})

            self.assertEqual(amount, 5.04)

    def test__get_to_be_interized__NotPayed(self):
        with self.assertRaises(InvestmentException) as ctx:
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user
                inv_id = self.IrModelData.get_object_reference(
                            cursor, uid, 'som_generationkwh', 'apo_0001'
                            )[1]
                current_interest = self.Emission.current_interest(cursor, uid)
                vals = {
                    'date_invoice': '2021-06-30',
                    'date_start': '2020-06-30',
                    'date_end': '2021-06-30',
                    'interest_rate': current_interest
                }
                self.Investment.get_to_be_interized(cursor, uid, inv_id, vals, {})

    def test__get_to_be_interized__previousPartialInterized(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]
            inv_obj = self.Investment.browse(cursor, uid, inv_id)
            inv_obj.write({'last_interest_paid_date' : '2020-12-31'})
            current_interest = self.Emission.current_interest(cursor, uid)
            vals = {
                'date_invoice': '2021-06-30',
                'date_start': '2020-06-30',
                'date_end': '2021-06-30',
                'interest_rate': current_interest
            }
            with self.assertRaises(InvestmentException) as e:
                to_be_interized = self.Investment.get_to_be_interized(cursor, uid, inv_id, vals, {})

            self.assertTrue('Cannot pay interest of a already paid interest' in e.exception.message)

    @mock.patch("som_generationkwh.investment_strategy.GenerationkwhActions._wait_and_update_signature_threaded")
    def test__create_signaturit_data__AllOkGKWH(self, mocked_update_sign):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]
            iban = 'ES7712341234161234567890'

            # the code makes a commit needed for production but useless at testing, and
            # it makes the DB dirty so we "deactivate" it
            cursor.commit = lambda: None
            id = self.Investment.create_from_form(cursor, uid,
                partner_id,
                '2017-01-01',
                2000,
                '10.10.23.1',
                iban,
                'emissio_genkwh',
                signaturit_data={
                    "id": "th1s-i5-a-f4ls3-1d",
                    "url": "https://app.sandbox.signaturit.com/document/th1s-i5-a-f4ls3-1d",
                    "documents": [{
                        "id": "th1s-i5-a-f4ls3-d0c-1d",
                        "file": {
                            "name": "Test_File.pdf",
                        },
                    }],
                }
            )
            investment = self.Investment.browse(cursor, uid, id)
            self.assertTrue(investment.signed_date)
            mocked_update_sign.assert_called()

# vim: et ts=4 sw=4