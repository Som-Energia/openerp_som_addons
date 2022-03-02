# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class GiscedataAtc(osv.osv):

    _name = 'giscedata.atc'
    _inherit = 'giscedata.atc'
    _order = 'id desc'

    def get_current_pending_state_info(self, cursor, uid, ids, context=None):
        """
            Get the info of the last history line by atc id.
        :return: a dict containing the info of the last history line of the
                 atc indexed by its id.
                 ==== Fields of the dict for each atc ===
                 'id': if of the last som.autoreclama.pending.state.history.atc
                 'pending_state_id': id of its pending_state
                 'change_date': date of change (also, date of the creation of
                                the line)
        """
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        pending_history_obj = self.pool.get('som.autoreclama.pending.state.history.atc')
        result = dict.fromkeys(ids, False)
        fields_to_read = ['pending_state_id', 'change_date', 'atc_id']
        for id in ids:
            res = pending_history_obj.search(
                cursor, uid, [('atc_id', '=', id)]
            )
            if res:
                # We consider the last record the first one due to order
                # statement in the model definition.
                values = pending_history_obj.read(
                    cursor, uid, res[0], fields_to_read)
                result[id] = {
                    'id': values['id'],
                    'pending_state_id': values['pending_state_id'][0],
                    'change_date': values['change_date'],
                }
            else:
                result[id] = False
        return result

    def _get_last_pending_state_from_history(self, cursor, uid, ids,
                                             field_name, arg, context=None):
        result = {k: {} for k in ids}
        last_lines = self.get_current_pending_state_info(cursor, uid, ids)
        for id in ids:
            if last_lines[id]:
                result[id]['pending_state'] = last_lines[id]['pending_state_id']
                result[id]['pending_state_date'] = last_lines[id]['change_date']
            else:
                result[id]['pending_state'] = False
                result[id]['pending_state_date'] = False
        return result

    def change_state(self, cursor, uid, ids, context):
        values = self.read(cursor, uid, ids, ['atc_id'])
        return [value['atc_id'][0] for value in values]

    _STORE_PENDING_STATE = {
        'som.autoreclama.pending.state.history.atc': (
            change_state, ['change_date'], 10
        )
    }

    _columns = {
        'pending_state': fields.function(
            _get_last_pending_state_from_history,
            method=True,
            type='many2one',
            obj='som.autoreclama.pending.state',
            string=u'Pending State',
            required=False,
            readonly=True,
            store=_STORE_PENDING_STATE,
            multi='pending'
        ),
        'pending_state_date': fields.function(
            _get_last_pending_state_from_history,
            method=True,
            type='datetime',
            store=_STORE_PENDING_STATE,
            string=u'Pending State Date',
            multi='pending'
        ),
        'pending_history_ids': fields.one2many(
            'som.autoreclama.pending.state.history.atc',
            'atc_id',
            _(u"Historic d'autoreclama"),
            readonly=True
        ),
    }

GiscedataAtc()
