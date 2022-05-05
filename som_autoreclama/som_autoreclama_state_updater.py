# -*- coding: utf-8 -*-
from osv import osv
from tqdm import tqdm
from tools.translate import _


class SomAutoreclamaStateUpdater(osv.osv_memory):

    _name = 'som.autoreclama.state.updater'

    def get_atc_candidates_to_update(self, cursor, uid, context=None):
        atc_obj = self.pool.get('giscedata.atc')
        search_params = [
            ('active', '=', True),
            ('state', '=', 'pending'),
            ('agent_actual', '=', '10'), # Distri
            ('autoreclama_state.is_last', '=', False),
            ]
        return atc_obj.search(cursor, uid, search_params)

    def update_atcs_if_possible(self, cursor, uid, ids, context=None):
        updated = []
        not_updated = []
        errors = []

        for atc_id in tqdm(ids):
            result, message = self.update_atc_if_possible(cursor, uid, atc_id, context)
            if result:
                updated.append(atc_id)
            elif result == False:
                not_updated.append(atc_id)
            else:
                errors.append(atc_id)

        return updated, not_updated, errors

    def update_atc_if_possible(self, cursor, uid, atc_id, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        history_obj = self.pool.get("som.autoreclama.state.history.atc")
        state_obj = self.pool.get("som.autoreclama.state")
        cond_obj = self.pool.get("som.autoreclama.state.condition")
        atc_data = atc_obj.get_autoreclama_data(cursor, uid, atc_id, context)

        state = atc_obj.read(cursor, uid, atc_id, ['autoreclama_state'], context)
        if 'autoreclama_state' in state and state['autoreclama_state']:
            autoreclama_state_id = state['autoreclama_state'][0]
        else:
            return False, _(u"Sense estat d'autoreclama inicial")

        cond_ids = cond_obj.search(cursor, uid, [
            ('state_id', '=', autoreclama_state_id),
            ('active', '=', True),
        ], order='priority', context=context)

        do_not_execute = context and context.get("search_only", False)
        for cond_id in cond_ids:
            if cond_obj.fit_atc_condition(cursor, uid, cond_id, atc_data):
                if do_not_execute:
                    return True, _(u'Testing')

                next_state_id = cond_obj.read(cursor, uid, cond_id, ['next_state_id'], context=context)['next_state_id'][0]
                action_result = state_obj.do_action(cursor, uid, next_state_id, atc_id, context)
                if action_result['do_change']:
                    history_obj.historize(cursor, uid, atc_id, next_state_id, None, action_result.get('created_atc', False), context)
                    return True, action_result.get('message', 'No message!!')
                else:
                    return None, action_result.get('message', 'No message!!')

        return False, _(u'No compleix cap condició activa, examinades {} condicions.').format(len(cond_ids))

    def state_updater(self, cursor, uid, context=None):
        if context is None:
            context = {}

        atc_ids = self.get_atc_candidates_to_update(cursor, uid, context)
        return self.update_atcs_if_possible(cursor, uid, atc_ids, context)


SomAutoreclamaStateUpdater()
