# -*- coding: utf-8 -*-
from osv import osv, fields
import pooler

class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'


    # Owner data
    def ownerNameInvestmentFromInvoice(self, cursor, uid, invoice_id):
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
