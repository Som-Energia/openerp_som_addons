# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _

STATES = [
    ('init', 'Estat Inicial'),
    ('finished', 'Estat Final')
]

class WizardCrearLecuresCalculades(osv.osv_memory):
    _name = 'wizard.crear.lectures.calculades'

    def crear_lectures_moure_lot(self, cursor, uid, ids, context=None):
        pol_o = self.pool.get('giscedata.polissa')
        pol_ids = context.get('active_ids', [])
        pol_o.crear_lectures_calculades(cursor, uid, pol_ids, context)
        self.write(cursor, uid, ids, {'state': 'finished'})

    _columns = {
        'state': fields.selection(STATES, _(u'Estat del wizard')),
    }

    _defaults = {
        'state': 'init'
    }

WizardCrearLecuresCalculades()
