# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
import datetime

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def investmentAmortization_notificationData(self, cursor, uid, id):
        report = ns()

        pool = pooler.get_pool(cursor.dbname)
        acc_inv = pool.get('account.invoice')
        gkwh_inv = pool.get('generationkwh.investment')

        report.receiptDate = datetime.datetime.today().strftime("%d-%m-%Y")
        report.ownerNif = '87654321-A'

        #Descripcio
        inversionId = acc_inv.search(cursor, uid, [
            ('id', '=', id)
        ])
        inversionDictName = acc_inv.read(cursor, uid, inversionId, ['name'])
        acc_inv_name = [a['name'] for a in inversionDictName]
        report.inversionName = acc_inv_name[0]

        #Get gkwh Inversion name/id
        gkwhInversionId = acc_inv.search(cursor, uid, [
            ('name', '=', report.inversionName)
        ])

        # Titular
        gkwhInversionDict = gkwh_inv.read(cursor, uid, gkwhInversionId, ['member_id'])
        gkwh_inv_ownerName = [a['member_id'] for a in gkwhInversionDict]
        report.ownerName = gkwh_inv_ownerName[1]

        #Inversion Initial
        gkwhInversionDict = gkwh_inv.read(cursor, uid, gkwhInversionId, ['nshares'])
        gkwh_inv_nshares = [a['nshares'] for a in gkwhInversionDict]
        report.inversionInitialAmount = gkwh_inv_nshares[0] * 100

        #Pending capital
        gkwhInversionDict = gkwh_inv.read(cursor, uid, gkwhInversionId, ['nshares'])
        gkwh_inv_nshares = [a['nshares'] for a in gkwhInversionDict]
        report.inversionInitialAmount = gkwh_inv_nshares[0] * 100
        report.inversionPendingCapital = '960,11'


        report.inversionBankAccount = 'ES25 0081 5273 6200 0103 ZZZZ'
        report.inversionPurchaseDate = '20-05-2015'
        report.inversionExpirationDate = '19-05-2040'

        report.amortizationName = "GKWH0000001-AMOR2017"
        report.amortizationAmount = '40,02'
        report.amortizationDate = '20-05-2017'
        report.amortizationNumPayment = '7'
        report.amortizationTotalPayments = '24'



        





        return report

AccountInvoice()
# vim: et ts=4 sw=4
