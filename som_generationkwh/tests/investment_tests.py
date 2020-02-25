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
from ..investment_strategy import PartnerException, InvestmentException
from freezegun import freeze_time

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
        self.Invoice = self.openerp.pool.get('account.invoice')
        self.InvoiceLine = self.openerp.pool.get('account.invoice.line')
        self.Emission = self.openerp.pool.get('generationkwh.emission')
        self.PaymentLine = self.openerp.pool.get('payment.line')
        self.PaymentOrder = self.openerp.pool.get('payment.order')
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
                    'nshares': 10,
                    'signed_date': '2017-01-06',
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2020-03-04',
                    'amortized_amount': 0.0,
                    'name': u'APO00001'
                })

    @freeze_time("2020-03-03")
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
                    '2017-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo')

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
                    'nshares': 40,
                    'signed_date': False,
                    'draft': True,
                    'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'),
                    'active': True,
                    'order_date': '2017-01-06',
                    'amortized_amount': 0.0,
                    'name': u'APO005000'
                })
            self.MailMockup.deactivate(cursor, uid)

    @freeze_time("2020-03-02")
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
                        '2017-01-06',
                        4000,
                        '10.10.23.123',
                        'ES7712341234161234567890',
                        'emissio_apo')

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
                        'nshares': 40,
                        'signed_date': False,
                        'draft': True,
                        'purchase_date': False,
                        'member_id': (1, u'Gil, Pere'),
                        'active': True,
                        'order_date': '2017-01-06',
                        'amortized_amount': 0.0,
                        'name': u'APO005000'
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

    @freeze_time("2020-03-03")
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
                    '2017-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo')

            self.assertMailLogEqual(self.MailMockup.log(cursor, uid), """\
                logs:
                - model: generationkwh.investment
                  id: {id}
                  template: aportacio_mail_creacio
                  from_id: [ {account_id} ]
                """.format(
                    id=inv_id,
                    account_id = self._invertirMailAccount(cursor, uid),
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

            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])

            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            investment = self.Investment.browse(cursor, uid, id)
            mandate_id = self.Investment.get_or_create_payment_mandate(cursor, uid,
                partner_id, iban, investment.emission_id.mandate_name, gkwh.creditorCode)
            partner_data = self.Partner.browse(cursor, uid, partner_id)
            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids[0], u"""\
                account_id: 410000{num_soci:0>6s} {p.name}
                amount_total: 2000.0
                amount_untaxed: 2000.0
                check_total: 2000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: 163500{num_soci:0>6s} {p.name}
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
                ))

    def test__create_initial_invoices__AllOkAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0001'
                        )[1]

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
                account_id: 410000{num_soci:0>6s} {p.name}
                amount_total: 1000.0
                amount_untaxed: 1000.0
                check_total: 1000.0
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: 163000{num_soci:0>6s} {p.name}
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
                journal_id: Factures Liquidació Aportacions
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
            emission_data = self.Emission.browse(cursor, uid, emission_id, ['name'])

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
            invoice_ids, errs =  self.Investment.create_initial_invoices(cursor, uid, [id])
            self.Investment.open_invoices(cursor, uid, invoice_ids)
            emission_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'emissio_apo'
                        )[1]
            emission_data = self.Emission.browse(cursor, uid, emission_id, ['name'])

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

            self.Investment.investment_actions(cursor, uid, investment.id).get_or_create_investment_account(cursor, uid, partner_id)

            partner = self.Partner.browse(cursor, uid, partner_id)
            self.assertEquals(partner.property_account_aportacions.code, '163000202001')
            self.assertEquals(partner.property_account_liquidacio.code, '410000202001')

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

            self.Investment.investment_actions(cursor, uid, investment.id).get_or_create_investment_account(cursor, uid, partner_id)

            partner = self.Partner.browse(cursor, uid, partner_id)
            self.assertEquals(partner.property_account_gkwh.code, '163500202001')
            self.assertEquals(partner.property_account_liquidacio.code, '410000202001')

    def test__amortize__oneAmortizationGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.MailMockup.activate(cursor, uid)
            investment_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0002'
                        )[1]
            inv = self.Investment.read(cursor, uid, investment_id)

            amortization_ids, errors = self.Investment.amortize(cursor, uid, '2021-10-13', [investment_id])

            self.assertEqual(len(amortization_ids), 1)
            self.assertEqual(len(errors), 0)
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
                    account_id = self._invertirMailAccount(cursor, uid),
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

    def test__get_investments_amount__withOldAportacions(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_0002'
                        )[1]

            amount = self.Investment.get_investments_amount(cursor, uid,
                member_id,
            )

            self.assertEqual(amount, 5000)

    @freeze_time("2020-03-03")
    def test__get_investments_amount__withOldAndNewAportacions(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            member_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'soci_0002'
                        )[1]
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor2'
                        )[1]
            inv_id = self.Investment.create_from_form(cursor, uid,
                    partner_id,
                    '2020-01-06',
                    4000,
                    '10.10.23.123',
                    'ES7712341234161234567890',
                    'emissio_apo')

            amount = self.Investment.get_investments_amount(cursor, uid,
                member_id,
            )

            self.assertEqual(amount, 9000)

    @freeze_time("2020-03-03")
    def test__get_max_investment__noInvestments_inTemporaLimitWithoutLimitInEmission(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
                    )[1]

            amount = self.Investment.get_max_investment(cursor, uid,
                partner_id, 'APO_202003'
            )
            #emission limit date is

            self.assertEqual(amount, 100000)

    @freeze_time("2020-03-13")
    def test__get_max_investment__noInvestments_outOfTemporaLimitWithoutLimitInEmission(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                    cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
                    )[1]

            amount = self.Investment.get_max_investment(cursor, uid,
                partner_id, 'APO_202003'
            )

            self.assertEqual(amount, 100000)

    @freeze_time("2020-03-03")
    def test__get_max_investment__noInvestments_inTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 5000,
                                 'limited_period_end_date': '2020-03-10',
                                 'current_total_amount_invested': 0})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202003'
                                                        )
            self.assertEqual(amount, 5000)

    @freeze_time("2020-03-13")
    def test__get_max_investment__noInvestments_outOfTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_noinversor2'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 5000,
                                 'limited_period_end_date': '2020-03-10',
                                 'current_total_amount_invested': 0})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202003'
                                                        )

            self.assertEqual(amount, 100000)

    @freeze_time("2020-03-03")
    def test__get_max_investment__withInvestments_inTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 1000,
                                 'limited_period_end_date': '2020-03-10'})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202003'
                                                        )
            self.assertEqual(amount, 0)

    @freeze_time("2020-03-13")
    def test__get_max_investment__withInvestments_outOfTemporaLimit(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
            )[1]
            emission_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_apo'
            )[1]
            self.Emission.write(cursor, uid, emission_id,
                                {'limited_period_amount': 1000,
                                 'limited_period_end_date': '2020-03-10'})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202003'
                                                        )

            self.assertEqual(amount, 94000)

    @freeze_time("2020-03-03")
    def test__get_max_investment__withOldInvestments_inTemporaLimit(self):
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
                                {'limited_period_amount': 1000,
                                 'limited_period_end_date': '2020-03-10'})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202003'
                                                        )
            self.assertEqual(amount, 1000)

    @freeze_time("2020-03-13")
    def test__get_max_investment__withOldInvestments_outOfTemporaLimit(self):
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
                                {'limited_period_amount': 500,
                                 'limited_period_end_date': '2020-03-10'})

            amount = self.Investment.get_max_investment(cursor, uid,
                                                        partner_id, 'APO_202003'
                                                        )

            self.assertEqual(amount, 95000)

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

    @freeze_time("2020-03-01")
    def test__get_max_investment__emissionDayBeforeOpen(self):
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
                                {'end_date': '2020-03-03', })

                amount = self.Investment.get_max_investment(cursor, uid,
                                                            partner_id, 'APO_202003'
                                                            )

        self.assertEqual(str(ctx.exception),'Emission not open yet')

    @freeze_time("2020-05-01")
    def test__get_max_investment__emissionDayAfterClosed(self):
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
                                {'end_date': '2020-04-30', })

                amount = self.Investment.get_max_investment(cursor, uid,
                                                            partner_id, 'APO_202003'
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


# vim: et ts=4 sw=4
