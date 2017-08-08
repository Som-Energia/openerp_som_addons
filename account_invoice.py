# coding=utf-8
from osv import osv


class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def unpay(self, cursor, uid, ids, amount, pay_account_id, period_id,
              pay_journal_id, context=None, name=''):

        res = super(AccountInvoice, self).unpay(
            cursor, uid, ids, amount, pay_account_id, period_id, pay_journal_id,
            context, name
        )
        print "Estem a la funcio filla"
        return res

    def pay_and_reconcile_group(self, cursor, uid, ids, pay_amount,
                                pay_account_id, period_id, pay_journal_id,
                                writeoff_acc_id, writeoff_period_id,
                                writeoff_journal_id, context=None, name=''):
        res = super(AccountInvoice, self).pay_and_reconcile_group(
            cursor, uid, ids, pay_amount, pay_account_id, period_id,
            pay_journal_id, writeoff_acc_id, writeoff_period_id,
            writeoff_journal_id, context, name
        )
        print "Estem a la funció filla"
        return res

    def get_investment(self, cursor, uid, inv_id):
        invoice = self.browse(cursor, uid, inv_id)

        Journal = self.pool.get('account.journal')
        journal_id_gen = Journal.search(cursor, uid, [
            ('code','=','GENKWH')
        ])[0]
        if invoice.journal_id.id != journal_id_gen:
            return None

        Investment = self.pool.get('generationkwh.investment')

        investment_ids = Investment.search(cursor, uid, [
            ('name','=',invoice.origin),
        ])

        if investment_ids:
            return investment_ids[0]

        return None

AccountInvoice()
# vim: et ts=4 sw=4
