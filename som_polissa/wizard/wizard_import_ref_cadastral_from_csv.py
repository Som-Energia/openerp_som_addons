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
        cups_obj = self.pool.get('giscedata.cups.ps')
        wiz = self.browse(cursor, uid, ids[0], context=context)
        csv_file = StringIO(base64.decodestring(wiz.csv_file))

        csv_reader = csv.reader(csv_file, delimiter=';')
        header = next(csv_reader)
        id_index = header.index('id')
        resultat_importacio_index = header.index('SUBCATEGORIA')

        col_indexs = {
            'ref_catastral': header.index('REFCAT'),
            'catas_tv': header.index('tipus_de_via'),
            'catas_nm': header.index('poblacio'),
            'catas_dp': header.index('codi_postal'),
            'catas_pu': header.index('PUERTA'),
            'catas_pt': header.index('PISO'),
            'catas_nv': header.index('NOMVIA'),
            'catas_np': header.index('provincia'),
            'catas_pnp': header.index('NUMVIA'),
            'catas_es': header.index('ESCALE'),
            'catas_bq': header.index('BLOQUE'),
        }

        for row in csv_reader:
            id_value = row[id_index]
            resultat_importacio = row[resultat_importacio_index]

            if not resultat_importacio:
                resultat_importacio = "Importat sense incidències"

            fields_to_update = ['ref_catastral', 'catas_tv', 'catas_nm', 'catas_dp',
                                'catas_pu', 'catas_pt', 'catas_nv', 'catas_np',
                                'catas_pnp', 'catas_es', 'catas_bq']
            dict_to_update = {}
            current = cups_obj.read(cursor, uid, int(id_value), fields_to_update)
            for field in fields_to_update:
                if wiz.overwrite or not current[field]:
                    dict_to_update[field] = row[col_indexs[field]].decode(
                        'iso-8859-1').encode('utf8')

            if not current['ref_catastral'] and dict_to_update:
                msg_importacio = resultat_importacio
            elif current['ref_catastral'] and dict_to_update:
                msg_importacio = ('Ja existia la referència catastral, s\'ha actualitzat ',
                                  'algun camp de l\'adreça')
            elif current['ref_catastral'] and not dict_to_update:
                msg_importacio = 'Ja existia la referència catastral i adreça completa'
            dict_to_update['importacio_cadastre_incidencies_origen'] = msg_importacio

            cups_obj.write(cursor, uid, int(id_value), dict_to_update)

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
