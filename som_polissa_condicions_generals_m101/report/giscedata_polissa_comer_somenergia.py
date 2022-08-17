# -*- coding: utf-8 -*-
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config


class report_webkit_html_proj(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        context['browse_reference'] = True

        super(report_webkit_html_proj, self).__init__(
            cursor, uid, name, context=context
        )
        self.localcontext.update({
            'cursor': cursor,
            'uid': uid,
            'company_id': self.localcontext['company'].id,
            'addons_path': config['addons_path'],
        })


webkit_report.WebKitParser(
    'report.somenergia.polissa_m101',
    'giscedata.switching',
    'som_polissa_condicions_generals_m101/report/condicions_particulars_m101.mako',
    parser=report_webkit_html_proj
)
