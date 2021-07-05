# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import tempfile
from datetime import date

STATES = [
    ('init', 'Estat Inicial'),
    ('finished', 'Estat Final')
]
class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        super(report_webkit_html, self).__init__(cursor, uid, name,
                                                 context=context)
        self.localcontext.update({
            'cursor': cursor,
            'uid': uid,
            'addons_path': config['addons_path'],
        })

class WizardCreateReport(osv.osv_memory):
    _name = 'wizard.create.report'

    _columns = {
        'state': fields.selection(STATES, _(u'Estat del wizard de imprimir report')),
    }

    _defaults = {
        'state': 'init'
    }

    def get_data(self, cursor, uid, ids, context=None):
        return [
            {
                'type': 'R101',
                'titol': 'R1 - 01',
                'data': '2021-01-01',
                'distribuidora': 'E-Redes',
                'procediment': 'R1 (reclamacio)',
                'pas': '01',
                'tipus_reclamacio': '003 - INCIDENCIA EN EQUIPOS DE MEDIDA',
                'codi_solicitud': '1564658',
                'text': 'Titular indica que el EdM esta apagado y no se ve la lectura. Solicita comprobacion.',
            },
            {
                'type': 'R102',
                'titol': 'R1 - 02',
                'data': '2021-01-10',
                'distribuidora': 'E-Redes',
                'procediment': 'R1 (reclamacio)',
                'pas': '02',
                'tipus_reclamacio': '003 - INCIDENCIA EN EQUIPOS DE MEDIDA',
                'codi_solicitud': '1564658',
                'text': 'La distrbuidora ha recibido la reclamacion',
            },
        ]

    def print_report(self, cursor, uid, ids, context=None):
        return {
            'type': 'ir.actions.report.xml',
            'model': 'wizard.create.report',
            'report_name': 'som.informe.report',
            'report_webkit': "'som_informe/report/report_som_informe.mako'",
            'webkit_header': 'som_informe_webkit_header',
            'groups_id': [],
            'multi': '0',
            'auto': '0',
            'header': '0',
            'report_rml': 'False',
        }

    def generate_report(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        erp_config = self.pool.get('res.config')
        folder_hash = erp_config.get(cursor, uid, 'google_drive_folder_technical_report', 'folder_hash')

        data = {
            'model': 'wizard.create.report',
            'id': wiz.id,
            'report_type': 'html2html'
        }
        report_printer = webkit_report.WebKitParser(
            'report.som.informe.report',
            'wizard.create.report',
            'som_informe/report/report_som_informe.mako',
            parser=report_webkit_html
        )
        document_binary = report_printer.create(
            cursor, uid, [wiz.id], data,
            context=context
        )

        gdm_obj = self.pool.get('google.drive.manager')
        file_name = '{}_informe_{}_{}'.format(str(date.today()), 'Reclama', 'CAT')
        with tempfile.NamedTemporaryFile(suffix='.html') as t:
            t.write(document_binary[0])
            t.flush()
            gdm_obj.uploadMediaToDrive(cursor, uid, file_name, t.name, folder_hash)

        wiz.write({'state': "finished"})


WizardCreateReport()