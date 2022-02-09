# -*- coding: utf-8 -*-

from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
from osv import osv
from yamlns import namespace as ns
from datetime import datetime


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
    'report.som.enviament.massiu',
    'som.enviament.massiu',
    'som_infoenergia/report/report_indexed_offer_template_pdf.mako',
    parser=report_webkit_html
)

class ReportIndexedOffer(osv.osv_memory):
    _name = 'report.indexed.offer'

    def get_report_data(self, cursor, uid, object, context=None):
        data = {}

        if object.extra_text:
            extra_text = eval(object.extra_text)
        else:
            extra_text = {}

        data['first_page'] = self.get_component_first_page_data(cursor, uid, object, extra_text, context)
        data['header'] = self.get_component_header_data(cursor, uid, object, extra_text, context)
        data['antecedents'] = self.get_component_antecedents_data(cursor, uid, object, extra_text, context)

        return ns.loads(ns(data).dump())

    def get_component_first_page_data(self, cursor, uid, object, extra_text, context):
        return {
            'nom_titular': object.partner_id.name,
        }

    def get_component_header_data(self, cursor, uid, object, extra_text, context):
        return {
            'data_oferta': datetime.today().strftime("%d-%m-%Y"),
            'codi_oferta': extra_text.get('codi_oferta', "ERROR EXTRA TEXT: sense codi oferta"),
            'nom_titular': object.partner_id.name,
        }

    def get_component_antecedents_data(self, cursor, uid, object, extra_text, context):
        return {
            'nom_titular': object.partner_id.name,
            'direccio': object.polissa_id.cups_direccio if object.polissa_id else "ERROR no polissa",
            'cups': object.polissa_id.cups.name if object.polissa_id else "ERROR no polissa",
            'consum_anual': extra_text.get("consum_anual", "ERROR EXTRA TEXT: sense consum anual"),
        }

    _columns = {}
    _defaults = {}

ReportIndexedOffer()