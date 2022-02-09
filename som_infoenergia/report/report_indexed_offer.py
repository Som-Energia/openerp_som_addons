# -*- coding: utf-8 -*-

from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
from osv import osv
from yamlns import namespace as ns
from datetime import datetime, timedelta


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
        data['objecte'] = self.get_component_objecte_data(cursor, uid, object, extra_text, context)
        data['cond_contr'] = self.get_component_cond_contr_data(cursor, uid, object, extra_text, context)
        data['power_prices'] = self.get_component_power_prices_data(cursor, uid, object, extra_text, context)
        data['energy_prices'] = self.get_component_energy_prices_data(cursor, uid, object, extra_text, context)
        data['tail_text'] = self.get_component_tail_text_data(cursor, uid, object, extra_text, context)
        data['conclusions'] = self.get_component_conclusions_data(cursor, uid, object, extra_text, context)
        return ns.loads(ns(data).dump())

    def get_component_first_page_data(self, cursor, uid, object, extra_text, context):
        return {'nom_titular': object.partner_id.name}

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

    def get_component_objecte_data(self, cursor, uid, object, extra_text, context):
        return {}

    def get_component_cond_contr_data(self, cursor, uid, object, extra_text, context):
        if object.lang == 'es_ES':
            return {'link': 'https://es.support.somenergia.coop/article/144-cuales-son-las-ventajas-de-ser-socio-a-de-som-energia'}
        else:
            return {'link': 'https://ca.support.somenergia.coop/article/186-quins-son-els-avantatges-de-ser-soci-a-de-som-energia'}

    def get_component_power_prices_data(self, cursor, uid, object, extra_text, context):
        return {
        }

    def get_component_energy_prices_data(self, cursor, uid, object, extra_text, context):
        return {
        }

    def get_component_tail_text_data(self, cursor, uid, object, extra_text, context):
        if object.polissa_id:
            if object.polissa_id.modcontractual_activa:
                data_limit_ingres = datetime.strptime(object.polissa_id.modcontractual_activa.data_final,"%Y-%m-%d") - timedelta(days=7)
                data_limit_ingres = data_limit_ingres.strftime("%d-%m-%Y")
            else:
                data_limit_ingres = "ERROR no mod con activa"
        else:
            data_limit_ingres = "ERROR no polissa"
        return {
            'data_limit_ingres': data_limit_ingres,
            'import_garantia': extra_text.get("import_garantia", "ERROR EXTRA TEXT: sense import garantia"),
        }

    def get_component_conclusions_data(self, cursor, uid, object, extra_text, context):
        return {}

    _columns = {}
    _defaults = {}

ReportIndexedOffer()