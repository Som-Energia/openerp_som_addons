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

        atc_obj = self.pool.get('giscedata.atc')

        msg = u""
        case_ids = context.get('active_ids', [])
        for case_id in reversed(case_ids):
            atc_id = atc_obj.create_related_atc_r1_case_via_wizard(cursor, uid, case_id, context)
            msg += "Creat el cas ATC amb id {} amb r1 029 associada a partir del cas ATC amb id {}\n".format(atc_id, case_id)

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