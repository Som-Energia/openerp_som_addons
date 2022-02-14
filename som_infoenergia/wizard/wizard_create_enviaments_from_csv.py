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
        'name': fields.char(_(u'Nom del fitxer'), size=256),
        'csv_file': fields.binary(_(u'Fitxer CSV'), required=True, help=_(u"Número de pòlissa de les pòlisses de les quals se'n vol crear un enviament")),
        'state': fields.selection(STATES, _(u'Estat del wizard de crear enviaments des de CSV')),
        'info': fields.text(_(u'Informació'), help=_(u"Només es creen enviaments de pòlisses Activa=Si"), size=256, readonly=True),
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
        vals = {'from_model': 'polissa_id'}
        csv_file = StringIO(base64.b64decode(wiz.csv_file))
        reader = csv.reader(csv_file)
        linies= list(reader)
        n_linies = len(linies)
        start = 0
        header = []
        if n_linies>0 and not linies[0][0].isdigit():
            if ';' in linies[0][0]:
                header = linies[0][0].split(';')
            else:
                header = linies[0]
            start=1

        pol_list= []
        result = {}
        for line in linies[start:]:
            if ';' in line[0]:
                line = line[0].split(';')
            pol_list.append(line[0])
            if not header:
                continue
            i = 1
            result_extra_info = {}
            for column in line[1:]:
                result_extra_info[header[i]] = column
                i += 1
            if result_extra_info:
                result[line[0]] = result_extra_info
        if result:
            vals['extra_text'] =  result

        lot_id = context.get('active_id', [])
        pol_ids = pol_obj.search(cursor, uid, [('name','in', pol_list)])
        lot_obj.create_enviaments_from_object_list(cursor, uid, lot_id, pol_ids, vals)
        msg = _(u"Es crearan els enviaments de {} pòlisses en segon pla".format(len(pol_ids)))
        wiz.write({'state': "finished", 'info': msg})
        return True

WizardCancelFromCSV()
