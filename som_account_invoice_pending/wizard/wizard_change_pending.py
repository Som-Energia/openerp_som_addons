# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
from tools.translate import _


class WizardChangePending(osv.osv_memory):
    """Wizard for changing pending state in invoices"""

    _inherit = 'wizard.change.pending'

    def onchange_new_pending(self, cursor, uid, ids, new_pending):
        res = False
        pending_obj = self.pool.get('account.invoice.pending.state')

        pending_days = pending_obj.read(cursor, uid, new_pending, ['pending_days'])['pending_days']

        return {'value': {'new_pending_days': pending_days},
                'domain': {},
                'warning': {},
                }


    def action_set_new_pending_remember_days(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not context.get('model', False):
            raise osv.except_osv(_(u'Error'),
                                 _(u'Cannot determine model'))

        wizard = self.browse(cursor, uid, ids[0])
        if not wizard.new_pending:
            raise osv.except_osv(
                _('Error!'),
                _('If you want to change the pending state'
                  ' the "new pending" field must be filled up')
            )
        model_ids = context.get('active_ids', [])
        model = context['model']
        model_obj = self.pool.get(model)
        new_pending_id = wizard.new_pending.id
        changed = 0

        #Search invoice pending history for previous days in the previous state
        pending_history_obj = self.pool.get('account.invoice.pending.history')
        fields_to_read = ['pending_state_id', 'change_date', 'invoice_id', 'days_to_next_state', 'end_date']
        for model_id in model_ids:
            changed += 1
            pstate_obj = self.pool.get('account.invoice.pending.state')
            pending_state_days = pstate_obj.read(
                cursor, uid, new_pending_id, ['pending_days']
            )
            res = pending_history_obj.search(
                cursor, uid, [('pending_state_id', '=', new_pending_id)], fields_to_read, order='change_date desc'
            )
            if res:
                days_in_prev_state = (datetime.strptime(res['end_date'], "%Y-%m-%d")).days - datetime.strptime(res['change_date'], "%Y-%m-%d")).days
                pending_state_days = pending_state_days - days_in_prev_state

            model_obj.set_pending(
                cursor, uid, [model_id], new_pending_id, context=context
            )
            pending_history_records = pending_history_obj.search(
                cursor, uid, [('invoice_id', '=', model_id)]
            )
            if pending_history_records:
                # We consider the last record the first one due to order
                # statement in the model definition.
                pending_history_obj.write(
                        cursor, uid, pending_history_records[0], {'days_to_next_state': pending_state_days})

        wizard.write({'changed_invoices': changed,
            'state': 'end'})


    _columns = {
        'new_pending_days': fields.integer(u'Dies pendents del nou estat'),
    }

    _defaults = {
        'new_pending_days': lambda *a: 0,
    }


WizardChangePending()