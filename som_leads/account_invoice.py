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

        lead_o = self.pool.get("som.soci.crm.lead")

        for id in ids:
            if self.browse(cursor, uid, id).state == 'paid':
                # Mirar si el lead està en stage Remesat
                lead = lead_o.search([('invoice_id', '=', id)])
                if lead.stage_id.name == 'Remesat':
                    pass
                # Cridar next_stage

        return res
