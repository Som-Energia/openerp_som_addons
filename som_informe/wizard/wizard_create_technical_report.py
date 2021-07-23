# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import tempfile
from datetime import date, datetime
from yamlns import namespace as ns
from gestionatr.defs import TABLA_80, TABLA_61
from gestionatr.utils import get_description


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
        file_name = '{}_informe_{}_{}'.format(str(date.today()), 'Reclama', 'CAT')
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
            pass
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

    def extract_switching_metadata(self, cursor, uid, sw_ids, context):
        if not isinstance(sw_ids, list):
            sw_ids = [sw_ids]
        result = []
        sw_obj = self.pool.get('giscedata.switching')

        for sw_id in sw_ids:
            sw_data = sw_obj.browse(cursor, uid, sw_id, context=context)

            for step in sw_data.step_ids:
                r_model,r_id = step.pas_id.split(',')
                model_obj = self.pool.get(r_model)
                pas = model_obj.browse(cursor, uid, int(r_id))

                extracted_data = self.extract_R1_metadata(cursor, uid, step.step_id.name, pas)
                if extracted_data:
                    result.append(extracted_data)

        return result

    def extract_R1_metadata(self, cursor, uid, step_name, step):
        result = {}
        result['date'] = step.date_created
        result['day'] = dateformat(step.date_created)
        result['create'] = dateformat(step.date_created, True)
        result['pas'] = step_name
        result['codi_solicitud'] = step.sw_id.codi_sollicitud
        result['titol'] = step.sw_id.proces_id.name + " - " + step.sw_id.step_id.name
        result['distribuidora'] = step.sw_id.partner_id.name
        if step_name == '01':
            result['type'] = 'R101'
            result['tipus_reclamacio'] = step.subtipus_id.name + " - " + step.subtipus_id.desc if step.subtipus_id else ''
            result['text'] = step.comentaris
        if step_name == '02':
            result['type'] = 'R102'
            result['rebuig'] = step.rebuig
            result['motiu_rebuig'] = step.motiu_rebuig
            result['codi_reclamacio_distri'] = step.codi_reclamacio_distri
            result['data_acceptacio'] = dateformat(step.data_acceptacio)
            result['data_rebuig'] = dateformat(step.data_rebuig)
        if step_name == '03':
            result['type'] = 'R103'
            result['codi_reclamacio_distri'] = step.codi_reclamacio_distri
            result['hi_ha_info_intermitja'] = step.hi_ha_info_intermitja
            result['desc_info_intermitja'] = step.desc_info_intermitja
            result['hi_ha_retipificacio'] = step.hi_ha_retipificacio
            result['tipologia_retifica'] = step.retip_tipus + step.retip_subtipus if step.retip_subtipus else '' + " - " + step.retip_desc
            result['hi_ha_sol_info_retip'] = step.hi_ha_sol_info_retip
            result['tipologia_sol_retip'] = step.retip_tipus + step.retip_subtipus if step.retip_subtipus else ''
            result['hi_ha_solicitud'] = step.hi_ha_solicitud
            result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
            result['comentaris_distri'] = step.comentaris
        if step_name == '04':
            result['type'] = 'R104'
            result['codi_reclamacio_distri'] = step.codi_reclamacio_distri
            result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
            result['comentaris_distri'] = step.comentaris
        if step_name == '05':
            result['type'] = 'R105'
            result['codi_reclamacio_distri'] = step.codi_reclamacio_distri
            result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
            result['comentaris_distri'] = step.comentaris
            result['resultat'] = get_description(step.resultat, 'TABLA_80')
            detail_obj = self.pool.get('giscedata.switching.detalle.resultado')
            ids = detail_obj.search(cursor, uid, [])
            vals = detail_obj.read(cursor, uid, ids, ['name', 'text'])
            details = dict([(v['name'], v['text']) for v in vals])
            result['detall_resultat'] = details.get(step.detall_resultat, step.detall_resultat)
        if step_name == '08':
            result['type'] = 'R108'
            result['codi_reclamacio_distri'] = step.codi_reclamacio_distri
        if step_name == '09':
            result['type'] = 'R109'
            result['codi_reclamacio_distri'] = step.codi_reclamacio_distri
            result['rebuig'] = step.rebuig
            result['motiu_rebuig'] = step.motiu_rebuig

        return result

    def get_columns(self, cursor, uid):
        pol_obj = self.pool.get('giscedata.polissa')
        no_function_fields = [field for field in pol_obj._columns if not isinstance(pol_obj._columns[field], (fields.function, fields.related, fields.property))]
        function_fields = [field for field in pol_obj._columns if isinstance(pol_obj._columns[field], (fields.function, fields.related, fields.property))]
        return function_fields, no_function_fields

WizardCreateTechnicalReport()