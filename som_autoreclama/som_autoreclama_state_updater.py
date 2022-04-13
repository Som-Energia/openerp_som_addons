# -*- coding: utf-8 -*-
from osv import osv

class SomAutoreclamaStateUpdater(osv.osv_memory):

    _name = 'som.autoreclama.state.updater'

    def get_atc_candidates_to_update(self, cursor, uid, context=None):
        atc_obj = self.pool.get('giscedata.atc')
        search_params = [
            ('active', '=', True),
            ('state', 'not in', ['cancel', 'done']),
            ('autoreclama_state.is_last', '=', False),
            ]
        return atc_obj.search(cursor, uid, search_params)

    def update_atcs_if_possible(self, cursor, uid, ids, context=None):
        updated = []
        not_updated = []

        for atc_id in ids:
            if self.update_atc_if_possible(cursor, uid, atc_id, context):
                updated.append(atc_id)
            else:
                not_updated.append(atc_id)

        return updated, not_updated

    def update_atc_if_possible(self, cursor, uid, atc_id, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        history_obj = self.pool.get("som.autoreclama.state.history.atc")
        state_obj = self.pool.get("som.autoreclama.state")
        cond_obj = self.pool.get("som.autoreclama.state.condition")
        atc_data = atc_obj.get_autoreclama_data(cursor, uid, atc_id, context)

        autoreclama_state_id = atc_obj.read(cursor, uid, atc_id, ['autoreclama_state'], context)['autoreclama_state'][0]
        cond_ids = cond_obj.search(cursor, uid,[
            ('state_id', '=', autoreclama_state_id),
            ('active', '=', True),
        ], order='priority', context=context)
        for cond_id in cond_ids:
            if cond_obj.fit_atc_condition(cursor, uid, cond_id, atc_data):
                try:
                    next_state_id = cond_obj.read(cursor, uid, cond_id, ['next_state_id'], context=context)['next_state_id'][0]
                    if state_obj.do_action(cursor, uid, next_state_id, atc_id, context):
                        history_obj.historize(cursor, uid, atc_id, next_state_id, None, context)
                        return True
                except Exception as e:
                    pass # TODO: handle this exception better and do nothing if error

        return False


    def state_updater(self, cursor, uid, context=None):
        if context is None:
            context = {}

        atc_ids = self.get_atc_candidates_to_update(cursor, uid, context)
        return self.update_atcs_if_possible(cursor, uid, atc_ids, context)

SomAutoreclamaStateUpdater()
