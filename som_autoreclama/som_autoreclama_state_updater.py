# -*- coding: utf-8 -*-
from osv import osv
from datetime import date

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
        for atc_id in ids:
            self.update_atc_if_possible(cursor, uid, atc_id, context)


    def update_atc_if_possible(self, cursor, uid, atc_id, context=None):


        # per el cas atc
        # comprovem si compleix alguna condició
        # si la compleix obtenim nou estat 
        # executar acció del nou estat
        # si no hi ha cap error
        # canviem l'estat al nou estat gravant l'historic


        atc_obj = self.pool.get("giscedata.atc")
        ash_obj = self.pool.get("som_autoreclama_state_history_atc")
        atc_data = atc_obj.get_autoreclama_data(cursor, uid, atc_id, context)
        atc = atc_obj.browse(cursor, uid, atc_id)

        for condition in atc.autoreclama_state.conditions_ids:
            if condition.fit_atc_condition(cursor, uid, atc_data):
                try:
                    next_state = condition.next_state
                    next_state.go_action(cursor, uid, atc_id)
                except:
                    pass
                ash_id = atc.autoreclama_history_ids[0]
                current_date = date.today().strftime("%d-%m-%Y")
                ash_obj.write(
                    cursor, 
                    uid, 
                    ash_id, 
                    {
                        'end_date': current_date
                    }
                )
                ash_obj.create(
                    cursor,
                    uid,
                    {
                        'atc_id': atc_id,
                        'autoreclama_state_id': next_state,
                        'change_date': current_date,
                    }
                )

    def state_updater(self, cursor, uid, context=None):

        if context is None:
            context = {}

        ids = self.get_atc_candidates_to_update(cursor, uid, context)
        self.update_atcs_if_possible(cursor, uid, ids, context)

        return True

SomAutoreclamaStateUpdater()
