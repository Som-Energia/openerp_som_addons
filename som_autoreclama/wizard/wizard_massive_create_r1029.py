# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from tools import config


class WizardMassiveCreateR1029(osv.osv_memory):
    _name = 'wizard.massive.create.r1029'
    # active_id giscedata.atc

    def action_create_r1029(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        ir_obj = self.pool.get('ir.model.data')
        atc_obj = self.pool.get('giscedata.atc')
        s_obj = self.pool.get('som.autoreclama.state')
        h_obj = self.pool.get('som.autoreclama.state.history.atc')

        disable_state_id = ir_obj.get_object_reference(cursor, uid, 'som_autoreclama', 'disabled_state_workflow_atc')[1]
        next_state_id = s_obj.browse(cursor, uid, disable_state_id)
        msg = u""
        case_ids = context.get('active_ids', [])
        for case_id in reversed(case_ids):
            atc_id = None
            try:
                atc_id = atc_obj.create_ATC_R1_029_from_atc_via_wizard(cursor, uid, case_id, context)
                msg += _("Cas {} creat el cas ATC amb id {} amb R1 029 associada\n").format(case_id, atc_id)
            except Exception as e:
                msg += _("Cas {} Error al crear el cas ATC R1 029 a partir del cas ATC: {}\n").format(case_id,str(e))

            if atc_id:
                try:
                    h_obj.historize(cursor, uid, case_id, next_state_id.id, None, atc_id, context)
                    msg += _("Cas {} estat canviat manualment a '{}'\n").format(case_id, next_state_id.name)
                except Exception as e:
                    msg += _("Cas {} error al canviar manualment a '{}' : {}\n").format(case_id, next_state_id.name, str(e))

        self.write(cursor, uid, ids, {'state': 'end', 'info': msg})

    _columns = {
        'state': fields.selection([('init', 'Init'), ('end', 'End')], 'State'),
        'info': fields.text('Informació', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: '',
    }

WizardMassiveCreateR1029()