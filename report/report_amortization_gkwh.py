# -*- coding: utf-8 -*-
from osv import osv, fields
import pooler

class AccountInvoice(osv.osv):

    #_name = 'amortization_gkwh_report'
    #_inherit = 'amortization_gkwh_report'
    _name = 'account.invoice'
    _inherit = 'account.invoice'






    #Report datas
    def titleReport(self):
        return 'Liquidació préstec Generation kWh'

    def dateReceiptReport(self):
        return '20-05-2017'

    #Investment datas
    def nameInvestmentFromInvoice(self, cursor, uid, invoice_id):
        return '2GKWH001'

    def ownerInvestmentFromInvoice(self, cursor, uid, invoice_id):
        return 'Pepito de Los Palotes'

    def amoutInitialInvestment(self,cursor, uid, investment_id):
        return '1.000,00 €'

    def datePurchaseInvestment(self, cursor, uid, investment_id):
        return '20-05-2015'

    def dateExpirationInvestment(seqlf, cursor, uid, investment_id):
        return '19-05-2040'

    #Amortitzation datas
    def amountAmortitzationFromInvoice(self, cursor, uid, invoice_id):
        return '40,00 €'

    def dateEndAmortizationFromInvoice(self, cursor, uid, invoice_id):
        return '20-05-2017'

    def numPaymentFromInvoice(self, cursor, uid, invoice_id):
        return '1 de 24'

    def capitalPendingFromInvestment(self, cursor, uid, investment_id):
        return '960,00 €'

    #AccountBank
    def bankAccountFromInvoice(self, cursor, uid, invoice_id):
        return 'ES25 0081 5273 6200 0103 9910'

AccountInvoice()
# vim: et ts=4 sw=4
