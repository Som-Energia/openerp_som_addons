# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from c2c_webkit_report import webkit_report


STATES = [
    ('init', 'Estat Inicial'),
    ('finished', 'Estat Final')
]

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
        wiz = self.browse(cursor, uid, ids[0])

        if not context:
            context = {}
        return {
            'type': 'ir.actions.report.xml',
            'model': 'som.informe.report',
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
            'model': 'giscedata.facturacio.factura',
            'id': fact_id,
            'report_type': 'webkit'
        }
        report_printer = webkit_report.WebKitParser(
            'report.som.informe.report.report.som.informe',
            'som.informe.report',
            'som_informe/report/report_som_informe.mako',
            parser=report_sxw.rml_parse
        )
        document_binary = report_printer.create(
            cursor, uid, [fact_id], data,
            context=ctx
        )

        wiz.write({'state': "finished"})

WizardCreateReport()