# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
import datetime
from dateutil.relativedelta import relativedelta

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def investmentAmortization_notificationData(self, cursor, uid, id):
        report = ns()

        pool = pooler.get_pool(cursor.dbname)
        acc_inv = pool.get('account.invoice')
        gkwh_inv = pool.get('generationkwh.investment')

        inversionId = acc_inv.search(cursor, uid, [
            ('id', '=', id)
        ])

        #Receipt Date
        inversionDictReceDat = acc_inv.read(cursor, uid, inversionId, ['date_invoice'])
        acc_inv_rec_date = [a['date_invoice'] for a in inversionDictReceDat]
        report.receiptDate = acc_inv_rec_date[0]


        report.ownerNif = '87654321-A'

        #Descripcio
        inversionDictName = acc_inv.read(cursor, uid, inversionId, ['name'])
        acc_inv_name = [a['name'] for a in inversionDictName]
        report.inversionName = acc_inv_name[0]

        #Get gkwh Inversion name/id
        gkwhInversionId = gkwh_inv.search(cursor, uid, [
            ('name', '=', report.inversionName)
        ])

        # Titular
        gkwhInversionDictOwner = gkwh_inv.read(cursor, uid, gkwhInversionId, ['member_id'])
        gkwh_inv_owner_name = [a['member_id'] for a in gkwhInversionDictOwner]
        report.ownerName = gkwh_inv_owner_name[0][1]

        #Inversion Initial
        gkwhInversionDictInitAmou = gkwh_inv.read(cursor, uid, gkwhInversionId, ['nshares'])
        gkwh_inv_nshares = [a['nshares'] for a in gkwhInversionDictInitAmou]
        report.inversionInitialAmount = gkwh_inv_nshares[0] * 100

        #Pending capital
        gkwhInversionDictPendCapt = gkwh_inv.read(cursor, uid, gkwhInversionId, ['amortized_amount'])
        gkwh_inv_amor_amou = [a['amortized_amount'] for a in gkwhInversionDictPendCapt]
        report.inversionPendingCapital = report.inversionInitialAmount - gkwh_inv_amor_amou[0]

        #Bank Account
        inversionDictBankAcco = acc_inv.read(cursor, uid, inversionId, ['partner_bank'])
        acc_inv_bank_acco = [a['partner_bank'] for a in inversionDictBankAcco]
        report.report.inversionBankAccount = acc_inv_bank_acco[0]

        #Purchase Date
        gkwhInversionDictPurDat = gkwh_inv.read(cursor, uid, gkwhInversionId, ['purchase_date'])
        gkwh_inv_pur_date = [a['purchase_date'] for a in gkwhInversionDictPurDat]
        report.inversionPurchaseDate = gkwh_inv_pur_date[0]

        #Expiration Date
        report.inversionExpirationDate = datetime.datetime.strptime(gkwh_inv_pur_date[0], "%Y-%m-%d").date() + relativedelta(years=+25)

        #Actual Amortization
        inversionDictActualAmor = acc_inv.read(cursor, uid, inversionId, ['number'])
        acc_inv_actu_amor = [a['number'] for a in inversionDictActualAmor]
        report.amortizationName = acc_inv_actu_amor[0]

        #Amortization Amount
        inversionDictAmount = acc_inv.read(cursor, uid, inversionId, ['amount_total'])
        acc_inv_amount = [a['amount_total'] for a in inversionDictAmount]
        report.amortizationAmount = acc_inv_amount[0]


        report.amortizationDate = '20-05-2017'
        report.amortizationNumPayment = '7'
        report.amortizationTotalPayments = '24'



        





        return report

AccountInvoice()
# vim: et ts=4 sw=4
