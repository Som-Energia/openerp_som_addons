# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
import datetime
from dateutil.relativedelta import relativedelta

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def investmentAmortization_notificationData_asDict(self, cursor, uid, ids):
        return dict(self.investmentAmortization_notificationData(cursor, uid, ids))

    def investmentAmortization_notificationData(self, cursor, uid, ids):
        report = ns()
        pool = pooler.get_pool(cursor.dbname)
        Invoice = pool.get('account.invoice')
        Investment = pool.get('generationkwh.investment')
        Partner = pool.get('res.partner')
        InvoiceLine = pool.get('account.invoice.line')


        account_id = ids[0]

        invoice = Invoice.read(cursor, uid, account_id, [
            'date_invoice',
            'partner_id',
            'name',
            'member_id',
            'invoice_line',
            'amount_total',
            'name',
            'partner_bank',
            ])

        partner = Partner.read(cursor, uid, invoice['partner_id'][0], [
            'vat',
            'name',
        ])

        # TODO: Find a more reliable way
        investment_id = Investment.search(cursor,uid, [
            ('name','=',invoice['name'].split('-AMOR')[0]),
        ])[0]

        investment = Investment.read(cursor,uid, investment_id, [
            'name',
            'nshares',
            'amortized_amount',
            'purchase_date',
            'last_effective_date',
        ])
        invoice_line = InvoiceLine.read(cursor,uid, invoice['invoice_line'][0],['note'])
        mutable_information = ns.loads(invoice_line['note'] or '{}')

        report.receiptDate = invoice['date_invoice']
        # TODO: non spanish vats not covered by tests
        report.ownerNif = partner['vat'][2:] if partner['vat'][:2]=='ES' else partner['vat']
        report.inversionName = investment['name']
        report.ownerName = partner['name']
        report.inversionPendingCapital = float(mutable_information.pendingCapital)
        # TODO: magic number shareValue, delegate on investment who knows it
        report.inversionInitialAmount = investment['nshares'] * 100
        report.inversionPurchaseDate = investment['purchase_date']
        report.inversionExpirationDate = investment['last_effective_date']
        report.amortizationAmount = invoice['amount_total']
        report.amortizationName = invoice['name']
        report.inversionBankAccount = invoice['partner_bank'][1]

        return report

        report.amortizationDate = '20-05-2017'
        report.amortizationNumPayment = '7'
        report.amortizationTotalPayments = '24'

        return report

AccountInvoice()
# vim: et ts=4 sw=4
