# -*- coding: utf-8 -*-
from c2c_webkit_report.webkit_report import WebKitParser
from report.report_sxw import rml_parse


WebKitParser(
    'report.giscedata.polissa',
    'giscedata.polissa',
    'som_polissa_condicions_generals/report/condicions_particulars.mako',
    parser=rml_parse
)
