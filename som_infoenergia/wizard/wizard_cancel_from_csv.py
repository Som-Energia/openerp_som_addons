# -*- coding: utf-8 -*-
import base64
import csv
from StringIO import StringIO

from osv import osv, fields
from tools.translate import _


STATES = [
    ('init', 'Estat Inicial'),
    ('finished', 'Estat Final')
]

class WizardCancelFromCSV(osv.osv_memory):
    _name = 'wizard.cancel.from.csv'
    _columns = {
        'name': fields.char('Filename', size=256),
        'csv_file': fields.binary('CSV File', required=True, help=_(u"Número de pòlissa de les pòlisses de les quals se'n vol cancel·lar l'enviament")),
        'state': fields.selection(STATES, _(u'Estat del wizard de cancelar enviaments des de CSV')),
        'reason': fields.text(_('Comentari'), size=256),
    }
    _defaults = {
        'state': 'init',
        'reason': ''
    }

    def cancel_from_file(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        lot_obj = self.pool.get('som.infoenergia.lot.enviament')
        wiz = self.browse(cursor, uid, ids[0], context=context)
        context['reason'] = wiz.reason
        csv_file = StringIO(base64.b64decode(wiz.csv_file))
        reader = csv.reader(csv_file)
        pol_list = [line[0] for line in list(reader)]

        lot_id = context.get('active_id', [])
        lot_obj.cancel_enviaments_from_polissa_names(cursor, uid, lot_id, pol_list, context)
        wiz.write({'state': "finished"})
        return True

WizardCancelFromCSV()
