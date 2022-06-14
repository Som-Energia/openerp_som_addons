# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from tools import config
from datetime import datetime

class WizardSomAutoreclamaSetDisableState(osv.osv_memory):
    _name = 'wizard.som.autoreclama.set.disable.state'

    def assign_state(self, cursor, uid, ids, context=None):
        h_obj = self.pool.get('som.autoreclama.state.history.atc')

        atc_ids = context.get('active_ids',[])

        ir_obj = self.pool.get('ir.model.data')
        disable_state_id = ir_obj.get_object_reference(cursor, uid, 'som_autoreclama', 'disabled_state_workflow_atc')[1]
        s_obj = self.pool.get('som.autoreclama.state')
        next_state_id = s_obj.browse(cursor, uid, disable_state_id)

        info = ""
        for atc_id in atc_ids:
            try:
                h_obj.historize(cursor, uid, atc_id, next_state_id.id, None, False, context)
                info += _("Cas {} estat canviat manualment a '{}'\n").format(atc_id, next_state_id.name)
            except Exception as e:
                info += _("Cas {} error al canviar manualment a '{}' : {}\n").format(atc_id, next_state_id.name, e.message)

        self.write(cursor, uid, ids, {'state':'end', 'info':info})
        return True

    _columns = {
        'state': fields.selection([('init', 'Init'), ('end', 'End')], 'State'),
        'info': fields.text('Informació', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: '',
    }

WizardSomAutoreclamaSetDisableState()