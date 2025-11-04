# -*- coding: utf-8 -*-
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config

class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        super(report_webkit_html, self).__init__(cursor, uid, name,
                                                 context=context)
        self.localcontext.update({
            'cursor': cursor,
            'uid': uid,
            'addons_path': config['addons_path'],
        })

webkit_report.WebKitParser(
    'report.amortization.gkwh',
    'account.invoice',
    'som_generationkwh/report/report_amortization_gkwh.mako',
    parser=report_webkit_html
)

webkit_report.WebKitParser(
    'report.contract.apo',
    'account.invoice',
    'som_generationkwh/report/report_contract_apo.mako',
    parser=report_webkit_html
)

# vim: et ts=4 sw=4
