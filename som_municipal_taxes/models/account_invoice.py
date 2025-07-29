# -*- coding: utf-8 -*-
from osv import osv


class AccountInvoice(osv.osv):
    _inherit = 'account.invoice'

    # Override the _amount_residual method to ensure residual amounts are calculated correctly
    def _amount_residual(self, cr, uid, ids, name, args, context=None):

        municipal_tax_journal_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid, 'som_municipal_taxes', 'municipal_tax_journal')[1]
        for inv_id in ids:
            inv = self.browse(cr, uid, inv_id, context=context)
            if inv.journal_id == municipal_tax_journal_id:
                for line_id in inv.move_id.ids:
                    line_obj = self.pool.get('account.move.line')
                    line_obj.write(cr, uid, line_id, {'currency_id': False}, context=context)
        return super(AccountInvoice, self)._amount_residual(
            cr, uid, ids, name, args, context=context)


AccountInvoice
