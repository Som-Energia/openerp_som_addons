# -*- coding: utf-8 -*-

from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config


class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        super(report_webkit_html, self).__init__(cursor, uid, name, context=context)
        self.localcontext.update(
            {
                "cursor": cursor,
                "uid": uid,
                "addons_path": config["addons_path"],
            }
        )


webkit_report.WebKitParser(
    "report.som.company.control",
    "res.company",
    "som_control_reports/report/company_control_report.mako",
    parser=report_webkit_html,
)
