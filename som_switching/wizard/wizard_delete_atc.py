# -*- coding: utf-8 -*-
from tools.translate import _
from osv import osv, fields

class WizardDeleteAtc(osv.osv_memory):
    _name = 'wizard.delete.atc'

    def delete_atc(self, cursor, uid, ids, context=None):
        atc_obj = self.pool.get('giscedata.atc')

        atc_cases = context.get('active_ids',[])
        res = atc_obj.delete_atc(cursor, uid, atc_cases, context)

        return {
            'type': 'ir.actions.act_window_close',
        }

WizardDeleteAtc()
