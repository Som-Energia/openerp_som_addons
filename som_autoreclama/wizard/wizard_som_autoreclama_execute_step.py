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
        atc_obj = self.pool.get('giscedata.atc')

        msg = u""
        atc_ids = context.get('active_ids', [])

        if atc_ids:
            atc_datas = atc_obj.read(cursor, uid, atc_ids, ['autoreclama_state'], context=context)
            for atc_data in atc_datas:
                atc_id = atc_data['id']
                atc_autoreclama_state = atc_data['autoreclama_state'][1] if atc_data['autoreclama_state'] else _(u'Sense estat inicial')
                updated, message = updtr_obj.update_atc_if_possible(cursor, uid, atc_id, context)
                if updated:
                    next_state = atc_obj.read(cursor, uid, atc_id, ['autoreclama_state'], context=context)['autoreclama_state'][1]
                    msg += _("Cas ATC amb id {} ha canviat d'estat: {} --> {}\n").format(atc_id, atc_autoreclama_state, next_state)
                    msg += _(" - {}\n").format(message)
                else:
                    msg += _("Cas ATC amb id {} no ha canviat d'estat: {}\n").format(atc_id, atc_autoreclama_state)
                    msg += _(" - {}\n").format(message)

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