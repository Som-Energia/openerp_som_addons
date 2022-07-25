# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from tools import config
from datetime import datetime

class WizardSomAutoreclamaSetManualState(osv.osv_memory):
    _name = 'wizard.som.autoreclama.set.manual.state'

    def assign_state(self, cursor, uid, ids, context=None):
        h_obj = self.pool.get('som.autoreclama.state.history.atc')

        atc_ids = context.get('active_ids',[])

        wiz = self.browse(cursor, uid, ids[0], context)

        info = ""
        for atc_id in atc_ids:
            try:
                h_obj.historize(cursor, uid, atc_id, wiz.next_state_id.id, None, False, context)
                info += _("Cas {} estat canviat manualment a '{}'\n").format(atc_id, wiz.next_state_id.name)
            except Exception as e:
                info += _("Cas {} error al canviar manualment a '{}' : {}\n").format(atc_id, wiz.next_state_id.name, e.message)

        self.write(cursor, uid, ids, {'state':'end', 'info':info})
        return True

    _columns = {
        'state': fields.selection([('init', 'Init'), ('end', 'End')], 'State'),
        'info': fields.text('Informació', readonly=True),
        'next_state_id': fields.many2one('som.autoreclama.state', 'Estat', required=True),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: '',
    }

WizardSomAutoreclamaSetManualState()