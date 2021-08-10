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
    AportacionsActions, GenerationkwhActions
)
from freezegun import freeze_time
import mock
from osv.osv import except_osv

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def send_sii_sync(self, cursor, uid, inv_id, context=None):
        return None

AccountInvoice()



class InvestmentStrategyTests(testing.OOTestCase):

    def setUp(self):
        self.MailMockup = self.openerp.pool.get('generationkwh.mailmockup')
        self.PEAccounts = self.openerp.pool.get('poweremail.core_accounts')
        self.Investment = self.openerp.pool.get('generationkwh.investment')
        self.Product = self.openerp.pool.get('product.product')
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.Partner = self.openerp.pool.get('res.partner')
        self.PartnerAddress = self.openerp.pool.get('res.partner.address')
        self.Invoice = self.openerp.pool.get('account.invoice')
        self.InvoiceLine = self.openerp.pool.get('account.invoice.line')
        self.Emission = self.openerp.pool.get('generationkwh.emission')
        self.PaymentLine = self.openerp.pool.get('payment.line')
        self.PaymentOrder = self.openerp.pool.get('payment.order')
        self.Soci = self.openerp.pool.get('somenergia.soci')
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

    def test__create_interest_invoices__AllOkAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            product_id = self.Product.search(cursor, uid, [
                ('default_code','=', 'APO_INT'),
            ])[0]
            taxes_id = self.Product.read(cursor, uid, product_id, ['supplier_taxes_id'])
            id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'apo_0003'
                        )[1]
            current_interest = self.Emission.current_interest(cursor, uid)
            vals = {
                'date_invoice': '2021-06-30',
                'interes': current_interest,
                'date_start': '2020-06-30',
                'date_end': '2021-06-30',
                'to_be_interized': 10,
                'interest_rate': current_interest
            }

            invoice_ids, errs =  self.Investment.create_interest_invoice(cursor, uid,
            [id], vals)

            invoice = self.Invoice.browse(cursor, uid, invoice_ids)
            self.assertFalse(errs)
            self.assertTrue(invoice_ids)
            investment = self.Investment.browse(cursor, uid, id)
            iban = 'ES7712341234161234567890'
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_aportacions'
                        )[1]
            emission_data = investment.emission_id
            partner_data = self.Partner.browse(cursor, uid, partner_id)

            self.assertInvoiceInfoEqual(cursor, uid, invoice_ids, u"""\
                account_id: 410000{num_soci:0>6s} {p.name}
                amount_total: 8.1
                amount_untaxed: 10.0
                check_total: 8.1
                date_invoice: '{invoice_date}'
                id: {id}
                invoice_line:
                - account_analytic_id: false
                  uos_id: PCE
                  account_id: 163000{num_soci:0>6s} {p.name}
                  name: 'Interessos fins a 30/06/2021 de {investment_name} '
                  discount: 0.0
                  invoice_id:
                  - {id}
                  - 'SI: {investment_name}'
                  origin: false
                  price_unit: 10.0
                  price_subtotal: 10.0
                  note:
                    interestDate: '2021-06-30'
                    interestRate: 1.0
                    investmentId: {investment_id}
                    investmentInitialAmount: 1000
                    investmentLastEffectiveDate: false
                    investmentName: APO00003
                    investmentPurchaseDate: '2020-03-12'
                  quantity: 1.0
                  product_id: '[APO_INT] Interessos Aportacions'
                  invoice_line_tax_id:
                  - {invoice_line_tax_id}
                journal_id: Factures Aportacions
                mandate_id: False
                name: {investment_name}-INT2021
                number: {investment_name}-INT2021
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
                invoice_date=datetime.today().strftime("%Y-%m-%d"),
                id=invoice_ids,
                iban='ES37 0151 7119 6002 1121 9240',
                year=2021,
                investment_name=investment.name,
                p=partner_data,
                num_soci= partner_data.ref[1:],
                investment_id=id,
                taxes_id=taxes_id,
                invoice_line_tax_id=invoice.invoice_line[0].invoice_line_tax_id[0].id
                ))
