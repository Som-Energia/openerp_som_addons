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

        investment_id = ids[0]

        investment = Invoice.read(cursor, uid, investment_id, [
            'date_invoice',
            'partner_id',
            'name',
            ])
        report.receiptDate = investment['date_invoice']

        #a partir de partner id
        partner = Partner.read(cursor, uid, investment['partner_id'][0], ['vat'])
        # TODO: non spanish vat not covered by tests
        report.ownerNif = partner['vat'][2:] if partner['vat'][:2]=='ES' else partner['vat']
        report.inversionName = investment['name']

        return report


        #Get gkwh Inversion name/id
        gkwhInversionId = Investment.search(cursor, uid, [
            ('name', '=', report.inversionName)
        ])

        # Titular
        gkwhInversionDictOwner = Investment.read(cursor, uid, gkwhInversionId, ['member_id'])
        gkwh_inv_owner_name = [a['member_id'] for a in gkwhInversionDictOwner]
        report.ownerName = gkwh_inv_owner_name[0][1]

        #Inversion Initial
        gkwhInversionDictInitAmou = Investment.read(cursor, uid, gkwhInversionId, ['nshares'])
        gkwh_inv_nshares = [a['nshares'] for a in gkwhInversionDictInitAmou]
        report.inversionInitialAmount = gkwh_inv_nshares[0] * 100

        #Pending capital
        gkwhInversionDictPendCapt = Investment.read(cursor, uid, gkwhInversionId, ['amortized_amount'])
        gkwh_inv_amor_amou = [a['amortized_amount'] for a in gkwhInversionDictPendCapt]
        report.inversionPendingCapital = report.inversionInitialAmount - gkwh_inv_amor_amou[0]

        #Bank Account
        inversionDictBankAcco = Invoice.read(cursor, uid, investment_id, ['partner_bank'])
        acc_inv_bank_acco = [a['partner_bank'] for a in inversionDictBankAcco]
        report.report.inversionBankAccount = acc_inv_bank_acco[0]

        #Purchase Date
        gkwhInversionDictPurDat = Investment.read(cursor, uid, gkwhInversionId, ['purchase_date'])
        gkwh_inv_pur_date = [a['purchase_date'] for a in gkwhInversionDictPurDat]
        report.inversionPurchaseDate = gkwh_inv_pur_date[0]

        #Expiration Date
        report.inversionExpirationDate = datetime.datetime.strptime(gkwh_inv_pur_date[0], "%Y-%m-%d").date() + relativedelta(years=+25)

        #Actual Amortization
        inversionDictActualAmor = Invoice.read(cursor, uid, investment_id, ['number'])
        acc_inv_actu_amor = [a['number'] for a in inversionDictActualAmor]
        report.amortizationName = acc_inv_actu_amor[0]

        #Amortization Amount
        inversionDictAmount = Invoice.read(cursor, uid, investment_id, ['amount_total'])
        acc_inv_amount = [a['amount_total'] for a in inversionDictAmount]
        report.amortizationAmount = acc_inv_amount[0]


        report.amortizationDate = '20-05-2017'
        report.amortizationNumPayment = '7'
        report.amortizationTotalPayments = '24'



        





        return report

AccountInvoice()
# vim: et ts=4 sw=4
