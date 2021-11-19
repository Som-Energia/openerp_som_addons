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

folder_data = {
    'R1' : {
        'config_id' : 'google_drive_folder_technical_report_R1',
        'config_value' : 'subfolder_R1_hash',
        'folder_name' : 'Informes de Reclamacions'},
    'ATR' : {
        'config_id' : 'google_drive_folder_technical_report_ATR',
        'config_value' : 'subfolder_ATR_hash',
        'folder_name' : "Informes d'ATR"},
    'FACT' : {
        'config_id' : 'google_drive_folder_technical_report_FACT',
        'config_value' : 'subfolder_FACT_hash',
        'folder_name' : 'Informes de Facturació'},
    'COBR' : {
        'config_id' : 'google_drive_folder_technical_report_COBR',
        'config_value' : 'subfolder_COBR_hash',
        'folder_name' : 'Informes de Cobraments'},
    'ERROR':{
        'config_id' : 'google_drive_folder_technical_report',
        'config_value' : 'folder_hash',
        'folder_name' : 'Informes ERROR'},
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
        'mostra_factura': fields.boolean('Mostra bloc de Factura'),
        #Gestió de Contractes block
        'mostra_A3': fields.boolean('A3'),
        'mostra_B1': fields.boolean('B1'),
        'mostra_B2': fields.boolean('B2'),
        'mostra_C1': fields.boolean('C1'),
        'mostra_C2': fields.boolean('C2'),
        'mostra_D1': fields.boolean('D1'),
        'mostra_E1': fields.boolean('E1'),
        'mostra_M1': fields.boolean('M1'),
        #Gestió de cobraments block
        'mostra_cobraments': fields.boolean('Mostra bloc de Gestió de Cobraments'),
    }

    _defaults = {
        'state': 'init'
    }

    def default_get(self, cr, uid, fields, context={}):
        res = {'state': 'init'}

        origin_model = context.get('origin')
        if origin_model == 'giscedata.polissa':
            res['polissa'] = context.get('active_id')

        return res

    def get_folder_data(self, cursor, uid, wiz, erp_config):
        subfolder = 'ERROR'

        atr_seleccionat = False
        if wiz.mostra_A3 or wiz.mostra_B1 or wiz.mostra_B2 or wiz.mostra_C1 or \
           wiz.mostra_C2 or wiz.mostra_D1 or wiz.mostra_E1 or wiz.mostra_M1 :
            atr_seleccionat = True

        if wiz.mostra_reclama and not atr_seleccionat:
            subfolder = 'R1'
        if atr_seleccionat:
            subfolder = 'ATR'
        if wiz.mostra_factura:
            subfolder = 'FACT'
        if wiz.mostra_cobraments:
            subfolder = 'COBR'

        if subfolder not in folder_data.keys():
            subfolder = 'ERROR'

        folder_hash = erp_config.get(cursor, uid, folder_data[subfolder]['config_id'], folder_data[subfolder]['config_value'])
        folder_name = folder_data[subfolder]['folder_name']

        return folder_hash, folder_name

    def generate_report(self, cursor, uid, ids, context=None):
        if not context: # force use the selected language in the report
            context = {}

        lang_id = self.read(cursor, uid, ids[0],['lang'])[0]['lang']
        lang_obj = self.pool.get('res.lang')
        lang_code = lang_obj.read(cursor, uid, lang_id, ['code'])['code']
        context['lang'] = lang_code

        wiz = self.browse(cursor, uid, ids[0], context=context)

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
        wiz = self.browse(cursor, uid, ids[0], context=context)

        erp_config = self.pool.get('res.config')
        folder_hash, folder_name = self.get_folder_data(cursor, uid, wiz, erp_config)

        file_name = '{}_informe_{}_{}'.format(str(date.today()), folder_name, lang_filename[lang_code])

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as t:
            t.write(document_binary[0])
            t.flush()
            g_response = gdm_obj.uploadMediaToDrive(cursor, uid, file_name, t.name, folder_hash)

        attach_obj = self.pool.get('ir.attachment')
        attach_obj.create(cursor, uid, {
            'res_model':'giscedata.polissa',
            'res_id': wiz.polissa.id,
            'name': g_response['name'],
            'link': 'https://docs.google.com/document/d/' + g_response['id'],
            }, context=context)

        return {'type': 'ir.actions.act_window_close'}

    # data generation
    def get_data(self, cursor, uid, id, context=None):
        if not context:
            context = {}

        wiz = self.browse(cursor, uid, id, context=context)

        seleccionats = []
        if wiz.mostra_reclama:
            seleccionats.append('R1')
        if wiz.mostra_A3:
            seleccionats.append('A3')
        if wiz.mostra_B1:
            seleccionats.append('B1')
        if wiz.mostra_B2:
            seleccionats.append('B2')
        if wiz.mostra_C1:
            seleccionats.append('C1')
        if wiz.mostra_C2:
            seleccionats.append('C2')
        if wiz.mostra_D1:
            seleccionats.append('D1')
        if wiz.mostra_E1:
            seleccionats.append('E1')
        if wiz.mostra_M1:
            seleccionats.append('M1')

        result_crono = []
        context['has_atr'] = len(seleccionats) > 0
        if seleccionats:
            search_params = [
                ('cups_polissa_id', '=' , wiz.polissa.id),
                ('proces_id.name', 'in', seleccionats),
                ]
            if wiz.date_from:
                search_params.append(('data_sollicitud', '>=', wiz.date_from))
            if wiz.date_to:
                search_params.append(('data_sollicitud', '<=', wiz.date_to))
            sw_obj = self.pool.get('giscedata.switching')
            sw_ids = sw_obj.search(cursor, uid, search_params)
            result_atr = self.extract_switching_metadata(cursor, uid, sw_ids, context)
            result_atr = sorted(result_atr, key=lambda k: k['date'])

            result_atr_head = self.extract_components_metadata(cursor, uid, wiz, ['atrHeader'], context)
            result_atr_foot = self.extract_components_metadata(cursor, uid, wiz, ['atrFooter'], context)
            result_crono = result_atr_head + result_atr + result_atr_foot

        result_factura = []
        if wiz.mostra_factura:
            result_factura = []

        result_cobra = []
        if wiz.mostra_cobraments:
            components_cobra = ['CollectHeader', 'CollectDetailsInvoices']
            result_cobra = self.extract_components_metadata(cursor, uid, wiz, components_cobra, context)

        result_ini = self.extract_components_metadata(cursor, uid, wiz, ['header'], context)
        result_end = self.extract_components_metadata(cursor, uid, wiz, ['footer'], context)

        result = result_ini + result_crono + result_factura + result_cobra + result_end
        return [ns(item) for item in result]

    # data extractors
    def factory_metadata_extractor(self, component_name):
        exec("from ..report.components."+component_name+" import "+component_name+";extractor = "+component_name+"."+component_name+"()")
        return extractor

    def metadata_extractor(self, cursor, uid, step, context=None):
        r_model,r_id = step.pas_id.split(',')
        model_obj = self.pool.get(r_model)
        pas = model_obj.browse(cursor, uid, int(r_id), context=context)
        component_name = step.proces_id.name+step.step_id.name
        extractor = self.factory_metadata_extractor(component_name)
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

    def extract_components_metadata(self, cursor, uid, wiz, components_names, context):
        result = []
        for component_name in components_names:
            extractor = self.factory_metadata_extractor(component_name)
            extracted_data = extractor.get_data(self, cursor, uid, wiz, context)
            if extracted_data:
                result.append(extracted_data)

        return result

    def get_columns(self, cursor, uid):
        pol_obj = self.pool.get('giscedata.polissa')
        no_function_fields = [field for field in pol_obj._columns if not isinstance(pol_obj._columns[field], (fields.function, fields.related, fields.property))]
        function_fields = [field for field in pol_obj._columns if isinstance(pol_obj._columns[field], (fields.function, fields.related, fields.property))]
        return function_fields, no_function_fields

WizardCreateTechnicalReport()