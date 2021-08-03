# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import tempfile
from datetime import date, datetime
from yamlns import namespace as ns

lang_filename = {
    'ca_ES' : 'CAT',
    'es_ES' : 'ES',
}

def dateformat(str_date, hours = False):
    if not str_date:
        return ""
    if not hours:
        return datetime.strptime(str_date[0:10],'%Y-%m-%d').strftime('%d-%m-%Y')
    return datetime.strptime(str_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')

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

class WizardCreateTechnicalReport(osv.osv_memory):
    _name = 'wizard.create.technical.report'

    _columns = {
        #Header
        'state': fields.selection(STATES, _(u'Estat del wizard de imprimir report')),
        'polissa': fields.many2one('giscedata.polissa', 'Contracte', required=True),
        'lang':  fields.many2one('res.lang', 'Language', required=True, select=1, help="Llengua de l'informe tècnic"),
        'date_from': fields.date('Data desde'),
        'date_to': fields.date('Data fins'),
        #Reclama block
        'mostra_reclama': fields.boolean('Mostra bloc de Reclama'),
        #Factura block
        'mostra_factura': fields.boolean('Mostra bloc de Reclama'),
        #Comptabilitat block
        'mostra_comptabilitat': fields.boolean('Mostra bloc de Reclama'),
        #Gestió de Contractes block
        'mostra_ATR': fields.boolean('Mostra bloc de Reclama'),
        #Gestió de cobraments block
        'mostra_cobraments': fields.boolean('Mostra bloc de Reclama'),
    }

    _defaults = {
        'state': 'init'
    }

    def generate_report(self, cursor, uid, ids, context=None):
        if not context: # force use the selected language in the report
            context = {}

        lang_id = self.read(cursor, uid, ids[0],['lang'])[0]['lang']
        lang_obj = self.pool.get('res.lang')
        lang_code = lang_obj.read(cursor, uid, lang_id, ['code'])['code']
        context['lang'] = lang_code

        wiz = self.browse(cursor, uid, ids[0], context=context)

        erp_config = self.pool.get('res.config')
        folder_hash = erp_config.get(cursor, uid, 'google_drive_folder_technical_report', 'folder_hash')

        data = {
            'model': 'wizard.create.report',
            'id': wiz.id,
            'report_type': 'html2html',
        }
        #Generate technical report
        report_printer = webkit_report.WebKitParser(
            'report.som.informe.report',
            'wizard.create.technical.report',
            'som_informe/report/report_som_informe.mako',
            parser=report_webkit_html
        )
        document_binary = report_printer.create(
            cursor, uid, [wiz.id], data,
            context=context
        )

        #Upload document to Drive
        gdm_obj = self.pool.get('google.drive.manager')
        file_name = '{}_informe_{}_{}'.format(str(date.today()), 'Reclama', lang_filename[lang_code])
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as t:
            t.write(document_binary[0])
            t.flush()
            gdm_obj.uploadMediaToDrive(cursor, uid, file_name, t.name, folder_hash)

        wiz.write({'state': "finished"})

    # data generation
    def get_data(self, cursor, uid, id, context=None):
        wiz = self.browse(cursor, uid, id, context=context)

        result  = []
        result.extend(self.extract_header_metadata(cursor, uid, wiz.polissa, context))
        result.extend(self.extract_footer_metadata(cursor, uid, wiz.polissa, context))
        sw_obj = self.pool.get('giscedata.switching')
        if wiz.mostra_reclama:
            search_params = [
                ('cups_id.id', '=', wiz.polissa.cups.id),
                ('proces_id.name', '=', 'R1'),
                ]
            if wiz.date_from:
                search_params.append(('date', '>=', wiz.date_from))
            if wiz.date_to:
                search_params.append(('date', '<=', wiz.date_to))
            sw_ids = sw_obj.search(cursor, uid, search_params)
            result.extend(self.extract_switching_metadata(cursor, uid, sw_ids, context))

        if wiz.mostra_factura:
            pass
        if wiz.mostra_cobraments:
            pass
        if wiz.mostra_ATR:
            search_params = [
                ('cups_id.id', '=', wiz.polissa.cups.id),
                ('proces_id.name', '=', 'A3'),
                ]
            if wiz.date_from:
                search_params.append(('date', '>=', wiz.date_from))
            if wiz.date_to:
                search_params.append(('date', '<=', wiz.date_to))
            sw_ids = sw_obj.search(cursor, uid, search_params)
            result.extend(self.extract_switching_metadata(cursor, uid, sw_ids, context))
        if wiz.mostra_comptabilitat:
            pass

        result = sorted(result, key=lambda k: k['date'])
        return [ns(item) for item in result]

    # data extractors
    def extract_header_metadata(self, cursor, uid, pol_data, context):
        return [{
            'type': 'header',
            'date': '1970-01-01',
            'data_alta': pol_data.data_alta,
            'contract_number': pol_data.name,
            'titular_name': pol_data.titular.name,
            'titular_nif': pol_data.titular_nif,
            'distribuidora': pol_data.distribuidora.name,
            'distribuidora_contract_number': pol_data.ref_dist,
            'cups': pol_data.cups.name,
            'cups_address': pol_data.cups_direccio,
        }]

    def extract_footer_metadata(self, cursor, uid, pol_data, context):
        return [{
            'type': 'footer',
            'date': '2040-01-01',
            'create_date': date.today().strftime("%d/%m/%Y"),
        }]

    def factory_metadata_extractor(self, step):
        component_name = step.proces_id.name+step.step_id.name
        exec("from ..report.components."+component_name+" import "+component_name+";extractor = "+component_name+"."+component_name+"()")
        return extractor

    def metadata_extractor(self, cursor, uid, step, context=None):
        r_model,r_id = step.pas_id.split(',')
        model_obj = self.pool.get(r_model)
        pas = model_obj.browse(cursor, uid, int(r_id), context=context)
        extractor = self.factory_metadata_extractor(step)
        return extractor.get_data(self, cursor, uid, pas)

    def extract_switching_metadata(self, cursor, uid, sw_ids, context):
        if not isinstance(sw_ids, list):
            sw_ids = [sw_ids]
        result = []
        sw_obj = self.pool.get('giscedata.switching')

        for sw_id in sw_ids:
            sw_data = sw_obj.browse(cursor, uid, sw_id, context=context)
            for step in sw_data.step_ids:
                extracted_data = self.metadata_extractor(cursor, uid, step, context)
                if extracted_data:
                    result.append(extracted_data)

        return result

    def get_columns(self, cursor, uid):
        pol_obj = self.pool.get('giscedata.polissa')
        no_function_fields = [field for field in pol_obj._columns if not isinstance(pol_obj._columns[field], (fields.function, fields.related, fields.property))]
        function_fields = [field for field in pol_obj._columns if isinstance(pol_obj._columns[field], (fields.function, fields.related, fields.property))]
        return function_fields, no_function_fields

WizardCreateTechnicalReport()