# -*- coding: utf-8 -*-
import csv
from osv import osv, fields

class WizardImportRefCadastralFromCSV(osv.osv_memory):
    _name = 'wizard.import.ref.cadastral.from.csv'

    def import_csv_file(self, cursor, uid, wiz_id, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, wiz_id, context=context)
        csv_file = base64.decodestring(wiz.csv_file)

        csv_reader = csv.reader(csv_file)

        header = next(csv_reader)
        id_index = header.index('id')
        refcat_index = header.index('refcat')

        for row in csv_reader:
            id_value = row[id_index]
            refcat_value = row[refcat_index]
            print id_value
            print refcat_value

        wiz.write(cursor, uid, {'state': 'end'}, context=context)

    _columns = {
        'csv_file': fields.binary(string='CSV File', required=True),
        'state': fields.selection(
            [('init', 'Initial'), ('end', 'End')], 'State'
        ),
    }

    _defaults = {
        'state': lambda *a: 'init'
    }

WizardImportRefCadastralFromCSV()