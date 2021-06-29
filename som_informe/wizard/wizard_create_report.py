# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import tempfile
from datetime import date
import os

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
                'type': 'test',
                'name1': 'aaaa',
                'name2': 'bbbb',
                'name3': 'cccc',
                'name4': 'dddd',
                'name5': 'eeee',
                'name6': 'ffff',
            },
            {
                'type': 'test2',
                'name1': 'aaaa',
                'name2': 'bbbb',
                'name3': 'cccc',
                'name4': 'dddd',
                'name5': 'eeee',
                'name6': 'ffff',
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
        active_id = context.get('active_id', 0)
        data = {
            'model': 'wizard.create.report',
            'id': wiz.id,
            'report_type': 'html2html'
        }
        report_printer = webkit_report.WebKitParser(
            #'report.wizard.create.report.som.informe.report',
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
            print t.name
            t.write(document_binary[0])
            t.flush()
            gdm_obj.uploadMediaToDrive(cursor, uid, file_name, t.name)

        wiz.write({'state': "finished"})


WizardCreateReport()