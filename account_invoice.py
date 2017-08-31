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
            if not self.is_investment_payment(cursor,uid,invoice_id):continue
            # TODO: pass date and moveline id
            moveline_id = self.get_investment_moveline(cursor,uid,invoice_id)
            Investment.mark_as_unpaid(cursor,uid,[investment_id],moveline_id)
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
            moveline_id = self.get_investment_moveline(cursor,uid,invoice_id)
            if not investment_id: continue
            if not self.is_investment_payment(cursor,uid,invoice_id):continue
            Investment.mark_as_paid(cursor,uid,[investment_id],today,moveline_id)
        return res

    def is_investment_payment(self, cursor, uid, invoice_id):
        invoice = self.read(cursor, uid, invoice_id, ['name'])
        return invoice and 'name' in invoice and str(invoice['name']).endswith("FACT")

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

    def get_investment_moveline(self, cursor, uid, invoice_id):
        '''Return moveline from invoice
        '''
        MoveLine = self.pool.get('account.move.line')
        invoice = self.read(cursor, uid, invoice_id,['move_id','name'])
        for moveline_id in  MoveLine.search(cursor, uid, [
            ('move_id','=',invoice['move_id'][0]),
            #('name', '=', invoice['name']),
            ('debit','=',0),
            ]):
            return moveline_id

AccountInvoice()


from addons.account.wizard.wizard_pay_invoice import _pay_and_reconcile as wizard_pay


class TesthelperPaymentWizard(osv.osv_memory):

    _name = 'generationkwh.payment.wizard.testhelper'
    _auto = False

    def pay(self, cursor, uid, invoice_id, movelinename):
        Invoice = self.pool.get('account.invoice')
        pending = Invoice.read(cursor, uid, invoice_id, ['residual'])['residual']
        wizard_pay(self, cursor, uid, data=dict(
            id = invoice_id,
            ids = [invoice_id],
            form = dict(
                amount=pending,
                name=movelinename,
                journal_id=15,
                period_id=92,
                date="2017-08-03",
            ),
        ), context={})

TesthelperPaymentWizard()



# vim: et ts=4 sw=4
