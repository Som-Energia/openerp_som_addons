# -*- coding: utf-8 -*-
from osv import osv
from datetime import datetime
from tools.translate import _


class WizardChangePending(osv.osv_memory):
    """Wizard for changing pending state in invoices"""

    _name = 'wizard.change.pending'
    _inherit = 'wizard.change.pending'

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
        context['eliminar_estats_anteriors'] = wizard.read(['eliminar_estats_anteriors'])[0]['eliminar_estats_anteriors']
        model_obj = self.pool.get(model)
        new_pending_id = wizard.new_pending.id
        changed = 0

        #Search invoice pending history for previous days in the previous state
        pending_history_obj = self.pool.get('account.invoice.pending.history')
        result = dict.fromkeys(ids, False)
        fields_to_read = ['pending_state_id', 'change_date', 'invoice_id', 'days_to_next_state']
        for id in model_ids:
            res = pending_history_obj.search(
                cursor, uid, [('pending_state_id', '=', new_pending_id)], order='change_date desc'
            )
            if res:
                # We consider the last record the first one due to order
                # statement in the model definition.
                values = pending_history_obj.search(
                    cursor, uid, res[0], fields_to_read)
                result[id] = {
                    'id': values['id'],
                    'pending_state_id': values['pending_state_id'][0],
                    'change_date': values['change_date'],
                    'days_to_next_state': values['days_to_next_state']
                }
            else:
                result[id] = False

        # Calculate the days to next state
        pstate_obj = self.pool.get('account.invoice.pending.state')
        for one_res in result:
            days_in_prev_state = (datetime.today() - datetime.strptime(one_res['change_date'], "%Y-%m-%d")).days
            pending_state_days = pstate_obj.read(
                cursor, uid, one_res['pending_state_id'], ['pending_days']
            )
            days_to_next_state = pending_state_days - days_in_prev_state
            if one_res['days_to_next_state'] is not None:
                days_to_next_state -= pending_state_days - one_res['days_to_next_state']


        for model_id in model_ids:
            model_obj.set_pending(
                cursor, uid, [model_id], new_pending_id, context=context
            )
            changed += 1
            res = pending_history_obj.search(
                cursor, uid, [('invoice_id', '=', model_id)]
            )
            if res:
                # We consider the last record the first one due to order
                # statement in the model definition.
                pending_history_obj.write(
                        cursor, uid, res[0], {'days_to_next_state':result[model_id]})


        wizard.write({'changed_invoices': changed,
                      'state': 'end'})
