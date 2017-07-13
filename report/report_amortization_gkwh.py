# -*- coding: utf-8 -*-
from osv import osv, fields
from yamlns import namespace as ns
import pooler

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def investmentAmortization_notificationData(self, cursor, uid, invoice_id):
        report = ns()

        report.receiptDate = self.investmentReceiptDate(cursor, uid, invoice_id)

        report.ownerName = self.ownerNameInvestmentFromInvoice(cursor, uid, invoice_id)
        report.ownerNif = self.ownerNifInvestmentFromInvoice(cursor, uid, invoice_id)

        report.inversionId = self.nameInvestmentFromInvoice(cursor, uid, invoice_id)
        report.inversionInitialAmount = self.amoutInitialInvestment(cursor, uid, invoice_id)
        report.inversionPendingCapital = self.capitalPendingFromInvestment(cursor, uid, invoice_id)
        report.inversionBankAccount = self.bankAccountFromInvoice(cursor, uid, invoice_id)
        report.inversionPurchaseDate = self.datePurchaseInvestment(cursor, uid, invoice_id)
        report.inversionExpirationDate = self.dateExpirationInvestment(cursor, uid, invoice_id)

        report.amortizationName = self.amortizationNameFromInvoice(cursor, uid, invoice_id)
        report.amortizationAmount = self.amortitzationAmountFromInvoice(cursor, uid, invoice_id)
        report.amortizationDate = self.amortizationEndDateFromInvoice(cursor, uid, invoice_id)
        report.amortizationNumPayment = self.amortizationNumPaymentFromInvoice(cursor, uid, invoice_id)
        report.amortizationTotalPayments = self.amortizationTotalPaymentFromInvoice(cursor, uid, invoice_id)

        return report

    def investmentReceiptDate(self, cursor, uid, invoice_id):
        import datetime
        return datetime.datetime.today().strftime("%d-%m-%Y")

    # Owner data
    def ownerNameInvestmentFromInvoice(self, cursor, uid, invoice_id):
        # invoice  id es una lista de ids!

        pool = pooler.get_pool(cursor.dbname)
        fact_obj = pool.get('giscedata.facturacio.factura')
        fact_reads = fact_obj.read(cursor, uid,invoice_id)

        #return repr(fact_reads)
        return 'Pepito de Los Palotes'

    def ownerNifInvestmentFromInvoice(self, cursor, uid, invoice_id):
        return '87654321-A'

    # Investment data
    def nameInvestmentFromInvoice(self, cursor, uid, invoice_id):
        return 'GKWH0000001'

    def amoutInitialInvestment(self,cursor, uid, investment_id):
        return '1.000,23'

    def capitalPendingFromInvestment(self, cursor, uid, investment_id):
        return '960,11'

    def bankAccountFromInvoice(self, cursor, uid, invoice_id):
        return 'ES25 0081 5273 6200 0103 ZZZZ'

    def datePurchaseInvestment(self, cursor, uid, investment_id):
        return '20-05-2015'

    def dateExpirationInvestment(seqlf, cursor, uid, investment_id):
        return '19-05-2040'

    # Amortization data
    def amortizationNameFromInvoice(self, cursor, uid, invoice_id):
        return "GKWH0000001-AMOR2017"

    def amortitzationAmountFromInvoice(self, cursor, uid, invoice_id):
        return '40,02'

    def amortizationEndDateFromInvoice(self, cursor, uid, invoice_id):
        return '20-05-2017'

    def amortizationNumPaymentFromInvoice(self, cursor, uid, invoice_id):
        return '7'

    def amortizationTotalPaymentFromInvoice(self, cursor, uid, invoice_id):
        return '29'

AccountInvoice()
# vim: et ts=4 sw=4
