# -*- coding: utf-8 -*-
from osv import osv, fields


class AccountInvoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    # Override the _amount_residual method to ensure residual amounts are calculated correctly
    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        if not context:
            context = {}
        if context.get('recursive', False):
            context['recursive'] = False
        else:
            municipal_tax_journal_id = self.pool.get('ir.model.data').get_object_reference(
                cr, uid, 'som_municipal_taxes', 'municipal_tax_journal')[1]
            data_inv = self.browse(cr, uid, ids, context=context)
            for inv in data_inv:
                if inv.journal_id.id == municipal_tax_journal_id and inv.move_id:
                    for line in inv.move_id.line_id:
                        line_obj = self.pool.get('account.move.line')
                        context['recursive'] = True
                        line_obj.write(cr, uid, [line.id], {'currency_id': None}, context=context)
        return super(AccountInvoice, self)._amount_residual(
            cr, uid, ids, name, args, context=context)

    def _get_invoice_line(self, cr, uid, ids, context=None):
        return super(AccountInvoice, self)._get_invoice_line(cr, uid, ids, context=context)

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        return super(AccountInvoice, self)._get_invoice_tax(cr, uid, ids, context=context)

    def _get_invoice_from_line(self, cr, uid, ids, context={}):
        municipal_tax_journal_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid, 'som_municipal_taxes', 'municipal_tax_journal')[1]
        for line in self.pool.get('account.move.line').browse(cr, uid, ids):
            if line.journal_id.id == municipal_tax_journal_id:
                return []
        return super(AccountInvoice, self)._get_invoice_from_line(
            cr, uid, ids, context=context)

    def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
        return super(AccountInvoice, self)._get_invoice_from_reconcile(
            cr, uid, ids, context=context)

    _columns = {
        'residual': fields.function(
            _amount_residual, method=True,
            digits=(16, 6), string='Residual',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 50),
                'account.invoice.tax': (_get_invoice_tax, None, 50),
                'account.invoice.line': (_get_invoice_line, [
                    'price_unit', 'invoice_line_tax_id', 'quantity', 'discount'], 50),
                'account.move.line': (_get_invoice_from_line, None, 50),
                'account.move.reconcile': (_get_invoice_from_reconcile, None, 50),
            },
            help="Remaining amount due."),
    }


AccountInvoice()


class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def create(self, cr, uid, vals, context=None, check=True):
        res = super(account_move_line, self).create(cr, uid, vals, context, check)
        move_line = self.browse(cr, uid, res)
        if move_line.currency_id:
            self.write(cr, uid, res, {'currency_id': None})

        return res

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        if 'currency_id' in vals.keys():
            vals['currency_id'] = None
        return super(account_move_line, self).write(
            cr, uid, ids, vals, context, check, update_check)


account_move_line()
