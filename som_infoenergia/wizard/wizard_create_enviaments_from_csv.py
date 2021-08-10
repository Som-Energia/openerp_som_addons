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
    _name = 'wizard.create.enviaments.from.csv'
    _columns = {
        'name': fields.char('Filename', size=256),
        'csv_file': fields.binary('CSV File', required=True, help=_(u"Número de pòlissa de les pòlisses de les quals se'n vol crear un enviament")),
        'state': fields.selection(STATES, _(u'Estat del wizard de crear enviaments des de CSV')),
        'info': fields.text(_('Informació'), help=_(u"Només es creen enviaments de pòlisses Activa=Si"), size=256, readonly=True),
    }
    _defaults = {
        'state': 'init',
    }

    def create_from_file(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        lot_obj = self.pool.get('som.infoenergia.lot.enviament')
        pol_obj = self.pool.get('giscedata.polissa')
        wiz = self.browse(cursor, uid, ids[0], context=context)

        csv_file = StringIO(base64.b64decode(wiz.csv_file))
        reader = csv.reader(csv_file)
        pol_list = [line[0] for line in list(reader)]

        lot_id = context.get('active_id', [])
        pol_ids = pol_obj.search(cursor, uid, [('name','in', pol_list)])
        lot_obj.create_enviaments_from_object_list(cursor, uid, lot_id, pol_ids, {'from_model': 'polissa_id'})
        msg = "Es crearan els enviaments de {} pòlisses en segon pla".format(len(pol_ids))
        wiz.write({'state': "finished", 'info': msg})
        return True

WizardCancelFromCSV()
