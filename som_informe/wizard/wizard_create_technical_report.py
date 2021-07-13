# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import tempfile
from datetime import date
from yamlns import namespace as ns

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
            #gdm_obj.uploadMediaToDrive(cursor, uid, file_name, t.name, folder_hash)

        wiz.write({'state': "finished"})

    # data generation
    def get_data(self, cursor, uid, id, context=None):
        wiz = self.browse(cursor, uid, id, context=context)
        pol_obj = self.pool.get('giscedata.polissa')
        pol_data = pol_obj.browse(cursor, uid, wiz.polissa)

        result = self.extract_header_metadata(cursor, uid, wiz.polissa.id)

        sw_obj = self.pool.get('giscedata.switching')
        if wiz.mostra_reclama:
            search_params = [
                ('date','>=', wiz.date_from),
                ('date', '<=', wiz.date_to),
                ('cups_id','=',pol_data.cups_id),
                ('proces_id.name', '=', 'R1'),
                ]
            sw_ids = sw_obj.search(cursor, uid, search_params)
            result.extend(self.extract_switching_metadata(cursor, uid, sw_ids))

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
    def extract_header_metadata(self, cursor, uid, pol_id):
        pol_obj = self.pool.get('giscedata.polissa')
        pol_data = pol_obj.browse(cursor, uid, pol_id)
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

    def extract_switching_metadata(self, cursor, uid, sw_ids):
        if not isinstance(sw_ids, list):
            sw_ids = [sw_ids]
        result = []
        sw_obj = self.pool.get('giscedata.switching')

        for _id in sw_ids:
            sw_data = sw.browse(cursor, uid, _id)
            result.append({
                #'type': sw_data.proces_id.name,
                'type': 'R101',
                'titol': sw_data.proces_id.name + " - " + sw_data.step_id.name,
                'date': sw_data.date,
                'distribuidora': sw_data.partner_id.name,
                'procediment': sw_data.procediment,
                'pas': sw_data.step_id.name,
                'tipus_reclamacio': sw_data.case_id.name,
                'codi_solicitud': sw_data.codi_sollicitud,
                'text': sw_data.additional_info,
            })

        return result


WizardCreateTechnicalReport()