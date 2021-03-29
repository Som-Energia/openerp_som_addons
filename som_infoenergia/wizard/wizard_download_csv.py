# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


STATES = [
    ('init', 'Estat Inicial'),
    ('finished', 'Estat Final')
]

class WizardDownloadCSV(osv.osv_memory):
    _name = 'wizard.infoenergia.download.csv'

    _columns = {
        'state': fields.selection(STATES, _(u'Estat del wizard de baixada de CSV')),
    }

    _defaults = {
        'state': 'init'
    }

    def download_csv(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        lot_obj = self.pool.get('som.infoenergia.lot.enviament')

        lot_id = context.get('active_id', [])

        wiz.write({'state': "finished"})
        lot = lot_obj.browse(cursor, uid, lot_id)
        lot.get_csv()

WizardDownloadCSV()
