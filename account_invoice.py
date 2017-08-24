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
        #TODO: Untested
        Investment = self.pool.get('generationkwh.investment')
        for invoice_id in ids:
            investment_id = self.get_investment(cursor,uid,invoice_id)
            if not investment_id: continue
            # TODO: pass date and moveline id
            Investment.mark_as_unpaid(cursor,uid,[investment_id])
        return res

    def pay_and_reconcile(self, cursor, uid, ids, pay_amount,
                                pay_account_id, period_id, pay_journal_id,
                                writeoff_acc_id, writeoff_period_id,
                                writeoff_journal_id, context=None, name=''):
        res = super(AccountInvoice, self).pay_and_reconcile(
            cursor, uid, ids, pay_amount, pay_account_id, period_id,
            pay_journal_id, writeoff_acc_id, writeoff_period_id,
            writeoff_journal_id, context, name
        )
        #TODO: Untested
        from datetime import date
        today = str(date.today()) #TODO date more real?
        Investment = self.pool.get('generationkwh.investment')

        for invoice_id in ids:
            investment_id = self.get_investment(cursor,uid,invoice_id)
            if not investment_id: continue
            Investment.mark_as_paid(cursor,uid,[investment_id],today)
        return res

    def get_investment_moveline(self, cursor, uid, invoice_id):
        '''Return moveline from invoice
        '''
        return
        MoveLine = self.pool.get('account.movement.line')
        Move = self.pool.get('account.movement')
        invoice = self.read(invoice_id,['move_id'])
        moveline_ids = MoveLine.search([
            ('move_id','=',invoice['move_id'][0]),
            ])

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
