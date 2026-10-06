# coding=utf-8
from osv import osv
from datetime import date
import generationkwh.investmentmodel as gkwh


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
            moveline_id = self.investment_last_moveline(cursor,uid,invoice_id)
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
        today = str(date.today()) #TODO date more real?
        Investment = self.pool.get('generationkwh.investment')
        for invoice_id in ids:
            investment_id = self.get_investment(cursor,uid,invoice_id)
            if not investment_id: continue
            moveline_id = self.investment_last_moveline(cursor,uid,invoice_id)
            if self.is_interest_payment(cursor, uid, invoice_id):
                Investment.mark_as_interested(cursor, uid, invoice_id)
            if self.is_investment_payment(cursor,uid,invoice_id):
               Investment.mark_as_paid(cursor,uid,[investment_id],today,moveline_id)
        return res

    def is_interest_payment(self, cursor, uid, invoice_id):
        ir_md_obj = self.pool.get('ir.model.data')
        apo_journal = ir_md_obj.get_object_reference(
            cursor, uid, 'som_generationkwh', 'apo_journal'
        )[1]
        invoice = self.browse(cursor, uid, invoice_id)
        return invoice and invoice.name and str(invoice.name).startswith("APO") and invoice.journal_id.id == apo_journal

    def is_investment_payment(self, cursor, uid, invoice_id):
        invoice = self.read(cursor, uid, invoice_id, ['name'])
        return invoice and 'name' in invoice and str(invoice['name']).endswith("-JUST")

    def get_investment(self, cursor, uid, inv_id):
        invoice = self.browse(cursor, uid, inv_id)
        Investment = self.pool.get('generationkwh.investment')
        Emission = self.pool.get('generationkwh.emission')
        investment_ids = Investment.search(cursor, uid, [
            ('name','=',invoice.origin),
        ])
        if not investment_ids:
            return None

        investment_data = Investment.read(cursor, uid, investment_ids[0], ['emission_id'])
        emission_data = Emission.read(cursor, uid, investment_data['emission_id'][0], ['journal_id'])

        if not invoice.journal_id: return None # TODO: Test missing

        Journal = self.pool.get('account.journal')
        journal_id_gen = emission_data['journal_id'][0]

        if invoice.journal_id.id != journal_id_gen:
            return None

        return investment_ids[0]


    def investment_last_moveline(self, cursor, uid, invoice_id):
        """
        For an investment invoice, gets the last moveline against
        non bridge account.

        Intended use is to recover the invoicing account movement
        after a payment or an unpayment. DO NOT USE FOR ANY OTHER
        PURPOSE WITHOUT A DOUBLE CHECK.
        """
        invoice = self.read(cursor, uid, invoice_id, [
            'journal_id',
            'name',
            'origin'
        ])
        Account = self.pool.get('account.account')
        Investment = self.pool.get('generationkwh.investment')
        Emission = self.pool.get('generationkwh.emission')
        inv_id = Investment.search(cursor, uid, [('name','=',invoice['origin'])])
        inv_data = Investment.read(cursor, uid, inv_id[0], ['emission_id'])
        em_data = Emission.read(cursor, uid, inv_data['emission_id'][0], ['bridge_account_payments_id'])
        account_id = em_data['bridge_account_payments_id'][0]

        MoveLine = self.pool.get('account.move.line')
        ids = MoveLine.search(cursor, uid, [
            ('ref', '=', invoice['name']),
            ('journal_id', '=', invoice['journal_id'][0]),
            ('account_id', '<>', account_id),
        ])
        moveline_ids = sorted(ids)

        if not moveline_ids: return False # TODO: Untested case

        return moveline_ids[-1]



AccountInvoice()




class TesthelperPaymentWizard(osv.osv_memory):

    _name = 'generationkwh.payment.wizard.testhelper'
    _auto = False

    def unpay(self, cursor, uid, invoice_id, movelinename):
        IrModelData = self.pool.get('ir.model.data')
        model, journal_id = IrModelData.get_object_reference(
            cursor, uid,
            'som_generationkwh', 'genkwh_journal',
        )
        Invoice = self.pool.get('account.invoice')
        invoice = Invoice.read(cursor, uid, invoice_id, [
            'amount_total',
            'account_id',
        ])

        Wizard = self.pool.get('wizard.unpay')
        from datetime import date
        wizard_id = Wizard.create(cursor, uid, dict(
            name = movelinename,
            date = date.today(),
            amount = invoice['amount_total'],
            pay_journal_id=journal_id,
            pay_account_id=invoice['account_id'],
        ))

        wizard = Wizard.browse(cursor, uid, wizard_id)
        wizard.unpay(dict(
            model = 'account.invoice',
            active_ids = [invoice_id],
        ))


    def pay(self, cursor, uid, invoice_id, movelinename):
        from addons.account.wizard.wizard_pay_invoice import _pay_and_reconcile as wizard_pay
        Invoice = self.pool.get('account.invoice')
        IrModelData = self.pool.get('ir.model.data')
        pending = Invoice.read(cursor, uid, invoice_id, ['residual'])['residual']
        model, journal_id = IrModelData.get_object_reference(
            cursor, uid,
            'som_generationkwh', 'genkwh_journal',
        )

        # The period
        Period = self.pool.get('account.period')
        from datetime import datetime
        today = datetime.today()
        period_name = today.strftime('%m/%Y')
        period_id = Period.search(cursor, uid, [
            ('name', '=', period_name),
            ])[0]

        wizard_pay(self, cursor, uid, data=dict(
            id = invoice_id,
            ids = [invoice_id],
            form = dict(
                amount=pending,
                name=movelinename,
                journal_id=journal_id,
                period_id=period_id,
                date="2017-08-03", # TODO: Magic date
            ),
        ), context={})


TesthelperPaymentWizard()



# vim: et ts=4 sw=4
