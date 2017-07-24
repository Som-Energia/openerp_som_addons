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

        invoice_line = InvoiceLine.read(cursor,uid, invoice['invoice_line'][0],['note'])
        mutable_information = ns.loads(invoice_line['note'] or '{}')

        report.receiptDate = invoice['date_invoice']
        # TODO: non spanish vats not covered by tests
        report.ownerNif = partner['vat'][2:] if partner['vat'][:2]=='ES' else partner['vat']
        report.inversionName = mutable_information.investmentName
        report.ownerName = partner['name']
        report.inversionPendingCapital = float(mutable_information.pendingCapital)
        report.inversionInitialAmount = mutable_information.investmentInitialAmount
        report.inversionPurchaseDate = mutable_information.investmentPurchaseDate
        report.inversionExpirationDate = mutable_information.investmentLastEffectiveDate
        report.amortizationAmount = invoice['amount_total']
        report.amortizationName = invoice['name']
        report.inversionBankAccount = invoice['partner_bank'][1]
        report.amortizationTotalPayments = mutable_information.amortizationTotalNumber
        report.amortizationDate = mutable_information.amortizationDate
        report.amortizationNumPayment = mutable_information.amortizationNumber

        return report

AccountInvoice()
# vim: et ts=4 sw=4
