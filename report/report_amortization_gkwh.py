# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler
import datetime

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def investmentAmortization_notificationData(self, cursor, uid, invoice_id):
        report = ns()

        report.receiptDate = datetime.datetime.today().strftime("%d-%m-%Y")

        report.ownerName = 'Pepito de Los Palotes'
        report.ownerNif = '87654321-A'

        report.inversionId = 'GKWH0000001'
        report.inversionInitialAmount = '1.000,23'
        report.inversionPendingCapital = '960,11'
        report.inversionBankAccount = 'ES25 0081 5273 6200 0103 ZZZZ'
        report.inversionPurchaseDate = '20-05-2015'
        report.inversionExpirationDate = '19-05-2040'

        report.amortizationName = "GKWH0000001-AMOR2017"
        report.amortizationAmount = '40,02'
        report.amortizationDate = '20-05-2017'
        report.amortizationNumPayment = '7'
        report.amortizationTotalPayments = '24'

        pool = pooler.get_pool(cursor.dbname)
        fact_obj = pool.get('giscedata.facturacio.factura')
        fact_reads = fact_obj.read(cursor, uid,invoice_id)


        return report

AccountInvoice()
# vim: et ts=4 sw=4
