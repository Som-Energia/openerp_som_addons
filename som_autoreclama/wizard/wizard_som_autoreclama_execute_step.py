# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from tools import config


class WizardSomAutoreclamaExecuteStep(osv.osv_memory):
    _name = 'wizard.som.autoreclama.execute.step'

    def execute_automation_step(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        updtr_obj = self.pool.get('som.autoreclama.state.updater')
        _, _, _, msg = updtr_obj.update_atcs_if_possible(cursor, uid, context.get('active_ids', []), context)
        self.write(cursor, uid, ids, {'state': 'end', 'info': msg})

    _columns = {
        'state': fields.selection([('init', 'Init'), ('end', 'End')], 'State'),
        'info': fields.text('Informació', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: '',
    }


WizardSomAutoreclamaExecuteStep()