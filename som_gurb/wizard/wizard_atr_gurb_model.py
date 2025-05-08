# -*- coding: utf-8 -*-
from osv import osv


class WizardATRGurbModel(osv.osv_memory):
    _name = 'wizard.atr.gurb.model'

    def list_all_pols(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get('som.gurb.cups')
        gurb_cups_ids = gurb_cups_obj.search(cursor, uid, [])

        pol_list = []
        gurb_cups_list = gurb_cups_obj.browse(cursor, uid, gurb_cups_ids)
        for gurb_cups in gurb_cups_list:
            pol_list.append(gurb_cups.polissa_id.id)

        return {
            'domain': [('cups_polissa_id', 'in', pol_list)],
            'name': 'Tots els casos ATR del GURB',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'giscedata.switching',
            'type': 'ir.actions.act_window',
            'view_id': False
        }


WizardATRGurbModel()
