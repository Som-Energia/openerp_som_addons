# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import date

class GiscedataAtc(osv.osv):

    _name = 'giscedata.atc'
    _inherit = 'giscedata.atc'
    _order = 'id desc'


    def set_autoreclama_history_deactivate(self, cursor, uid, ids, context=None):
        pass

    def create(self, cursor, uid, ids, context=None):
        super(GiscedataAtc, self).create(cursor, uid, ids, context=context)
        imd_obj = self.get('ir.model.data')
        correct_state_id = imd_obj.get_object_reference(
                cursor, uid, 'som_autoreclama', 'correct_state_workflow_atc'
        )[1]

        atch_obj = self.get('som.autoreclama.state.history.atc')
        for atc_id in ids:
            atch_obj.create(
                cursor,
                uid,
                {
                    'atc_id': atc_id,
                    'autoreclama_state_id': correct_state_id,
                    'change_date': date.today().strftime("%d-%m-%Y"),
                }
            )

    def get_current_autoreclama_state_info(self, cursor, uid, ids, context=None):
        """
            Get the info of the last history line by atc id.
        :return: a dict containing the info of the last history line of the
                 atc indexed by its id.
                 ==== Fields of the dict for each atc ===
                 'id': if of the last som.autoreclama.state.history.atc
                 'autoreclama_state_id': id of its state
                 'change_date': date of change (also, date of the creation of
                                the line)
        """
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        history_obj = self.pool.get('som.autoreclama.state.history.atc')
        result = dict.fromkeys(ids, False)
        fields_to_read = ['autoreclama_state_id', 'change_date', 'atc_id']
        for id in ids:
            res = history_obj.search(
                cursor, uid, [('atc_id', '=', id)]
            )
            if res:
                # We consider the last record the first one due to order
                # statement in the model definition.
                values = history_obj.read(
                    cursor, uid, res[0], fields_to_read)
                result[id] = {
                    'id': values['id'],
                    'autoreclama_state_id': values['autoreclama_state_id'][0],
                    'change_date': values['change_date'],
                }
            else:
                result[id] = False
        return result

    def _get_last_autoreclama_state_from_history(self, cursor, uid, ids, field_name, arg, context=None):
        result = {k: {} for k in ids}
        last_lines = self.get_current_autoreclama_state_info(cursor, uid, ids)
        for id in ids:
            if last_lines[id]:
                result[id]['autoreclama_state'] = last_lines[id]['autoreclama_state_id']
                result[id]['autoreclama_state_date'] = last_lines[id]['change_date']
            else:
                result[id]['autoreclama_state'] = False
                result[id]['autoreclama_state_date'] = False
        return result

    def change_state(self, cursor, uid, ids, context):
        values = self.read(cursor, uid, ids, ['atc_id'])
        return [value['atc_id'][0] for value in values]

    _STORE_STATE = {
        'som.autoreclama.state.history.atc': (
            change_state, ['change_date'], 10
        )
    }

    _columns = {
        'autoreclama_state': fields.function(
            _get_last_autoreclama_state_from_history,
            method=True,
            type='many2one',
            obj='som.autoreclama.state',
            string=_(u'Estat autoreclama'),
            required=False,
            readonly=True,
            store=_STORE_STATE,
            multi='autoreclama'
        ),
        'autoreclama_state_date': fields.function(
            _get_last_autoreclama_state_from_history,
            method=True,
            type='date',
            string=_(u"última data d'autoreclama"),
            required=False,
            readonly=True,
            store=_STORE_STATE,
            multi='autoreclama'
        ),
        'autoreclama_history_ids': fields.one2many(
            'som.autoreclama.state.history.atc',
            'atc_id',
            _(u"Historic d'autoreclama"),
            readonly=True
        ),
    }

GiscedataAtc()
