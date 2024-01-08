# -*- coding: utf-8 -*-
import csv
import base64
from StringIO import StringIO
from osv import osv, fields

class WizardImportRefCadastralFromCSV(osv.osv_memory):
    _name = 'wizard.import.ref.cadastral.from.csv'

    def import_ref_cadastral_csv(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0], context=context)
        csv_file = StringIO(base64.decodestring(wiz.csv_file))

        csv_reader = csv.reader(csv_file, delimiter=';')
        header = next(csv_reader)
        id_index = header.index('id')
        refcat_index = header.index('REFCAT')
        subcat_index = header.index('SUBCATEGORIA')
        cups_obj = self.pool.get('giscedata.cups.ps')

        for row in csv_reader:
            id_value = row[id_index]
            refcat_value = row[refcat_index]
            subcat_value = row[subcat_index]
            if not subcat_value:
                subcat_value = "Importat sense incidències"

            current = cups_obj.read(cursor, uid, int(id_value), ['ref_catastral'])
            if wiz.overwrite or not current['ref_catastral']:
                cups_obj.write(cursor, uid, int(id_value), {'ref_catastral': refcat_value,
                'importacio_cadastre_incidencies_origen' : subcat_value})
            elif current['ref_catastral']:
                cups_obj.write(cursor, uid, int(id_value), {'importacio_cadastre_incidencies_origen' : 'Ja existia la referència catastral'})


        wiz.write({'state': 'end'})

    _columns = {
        'csv_file': fields.binary(string='CSV File', required=True),
        'state': fields.selection(
            [('init', 'Initial'), ('end', 'End')], 'State'
        ),
        'overwrite': fields.boolean('Sobreescriure'),
    }

    _defaults = {
        'state': lambda *a: 'init'
    }

WizardImportRefCadastralFromCSV()