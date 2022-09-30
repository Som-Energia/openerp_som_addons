# -*- coding: utf-8 -*-
from autoworker import AutoWorker
import base64
from c2c_webkit_report import webkit_report
from datetime import datetime
from oorq.decorators import job
from oorq.oorq import ProgressJobsPool
import os
from osv import osv, fields
from report import report_sxw
from zipfile import ZipFile

class WizardLlibreRegistreSocis(osv.osv_memory):
    """Assistent per generar registre de socis"""

    _name = 'wizard.llibre.registre.socis'

    def generate_report(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0])
        context['date_from'] = wiz.date_from
        context['date_to'] = wiz.date_to
        j_pool = ProgressJobsPool(logger_description="print_report")
        aw = AutoWorker(queue="print_report", default_result_ttl=24 * 3600, max_procs=1)
        j_pool.add_job(self.generate_one_report(cursor, uid, ids, context))
        aw.work()
        return {}

    @job(queue="print_report", timeout=3000)
    def generate_one_report(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0])

        dades = self.get_report_data(cursor, uid, ids, context)
        summary_dades = self.get_report_summary(dades)

        header = {}
        header['date_from'] = context['date_from']
        header['date_to'] = context['date_to']

        document_binary = self.generate_report_pdf(cursor, uid, ids, dades, header, context)
        document_binary_summary = self.generate_report_summary_pdf(cursor, uid, ids, summary_dades, header, context)

        path = "/tmp/reports"
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except OSError:
                print ("Creation of the directory %s failed" % path)

        path_filename, filename = self.create_file(path, "llibre_registre_socis_", header['date_to'][:4],document_binary[0])
        path_filenamesummary, filenamesummary = self.create_file(path, "resum_llibre_registre_socis_", header['date_to'][:4],document_binary_summary[0])

        filename_zip = path + "/llibre_registre_socis_" + str(header['date_to'][:4]) + ".zip"
        zipObj = ZipFile(filename_zip, 'w')
        zipObj.write(path_filename, filename)
        zipObj.write(path_filenamesummary, filenamesummary)
        zipObj.close()

        ar_obj = self.pool.get('async.reports')
        datas = ar_obj.get_datas_email_params(cursor, uid, {}, context)
        ar_obj.send_mail(cursor, uid, datas['from'], filename_zip, datas['email_to'], filename_zip.split("/")[-1])

    def create_file(self, path, file_header, date, document):
        filename = file_header + str(date) + ".pdf"
        path_filename = path + "/" + filename

        f = open(path_filename, 'wb+' )
        try:
            bits = base64.b64decode(base64.b64encode(document))
            f.write(bits)
        finally:
            f.close()

        return path_filename,filename

    def generate_report_pdf(self, cursor, uid, ids, dades, header, context):
        report_printer = webkit_report.WebKitParser(
            'report.somenergia.soci.report_llibre_registre_socis',
            'somenergia.soci',
            'som_generationkwh/report/report_llibre_registre_socis.mako',
            parser=report_sxw.rml_parse
        )
        return self.generate_report_document(cursor, uid, ids, dades, header, report_printer, context)

    def generate_report_summary_pdf(self, cursor, uid, ids, summary_dades, header, context):
        report_printer = webkit_report.WebKitParser(
            'report.somenergia.soci.report_llibre_registre_socis_summary',
            'somenergia.soci',
            'som_generationkwh/report/report_llibre_registre_socis_summary.mako',
            parser=report_sxw.rml_parse
        )
        return self.generate_report_document(cursor, uid, ids, summary_dades, header, report_printer, context)

    def generate_report_document(self, cursor, uid, ids, dades, header, report_printer, context):
        data = {
            'model': 'giscedata.facturacio.factura',
            'report_type': 'webkit',
            'dades': dades,
            'header': header,
        }
        context['webkit_extra_params'] = '--footer-right [page]'
        document_binary = report_printer.create(
            cursor, uid, ids, data,
            context=context
        )
        if not document_binary:
            raise Exception("We can't create the report")

        return document_binary

    def get_report_summary(self, dades):
        numero_altes = 0
        numero_baixes = 0
        total_import_voluntari = 0
        total_import_voluntari_retirat = 0

        for dada in dades:
            for inversio in dada['inversions']:
                if inversio['concepte'] == u'Obligatoria':
                    if inversio['import'] > 0:
                        numero_altes += 1
                    else:
                        numero_baixes += 1
                elif inversio['concepte'] == u'Voluntaria':
                    if inversio['import'] > 0:
                        total_import_voluntari += inversio['import']
                    else:
                        total_import_voluntari_retirat += inversio['import'] * -1
        return {
                'numero_altes': numero_altes,
                'numero_baixes': numero_baixes,
                'total_import_voluntari': total_import_voluntari,
                'total_import_voluntari_retirat':total_import_voluntari_retirat,
                }

    def get_report_data(self, cursor, uid, ids, context=None):
        soci_obj = self.pool.get('somenergia.soci')
        socis = soci_obj.search(cursor, uid, [('active','=',True)])
        socis.sort()
        values = []
        for soci in socis:
            header = self.get_soci_values(cursor, uid, soci, context)
            apos = self.get_aportacions_obligatories_values(cursor, uid, soci, context)
            apo_vol = self.get_aportacions_voluntaries_values(cursor, uid, soci, context)
            quadre_moviments = sorted(iter(apos + apo_vol), key=lambda item: item['data'])
            total = 0
            for it in iter(quadre_moviments):
                it['total'] = total + it['import']
                total = it['total']
            header.update({'inversions': quadre_moviments})
            values.append(header)

	return values

    def get_soci_values(self, cursor, uid, soci, context=None):
        soci_obj = self.pool.get('somenergia.soci')
        data = soci_obj.read(cursor, uid, soci, ['ref','name','vat',
            'www_email', 'www_street','www_zip', 'www_provincia',
            'date','data_baixa_soci', 'www_municipi'])
        singles_soci_values = {
            'tipus': 'Consumidor',
            'num_soci': data['ref'],
            'nom': data['name'],
            'dni': data['vat'][2:] if data['vat'] else False,
            'email': data['www_email'] if data['www_email'] else '',
            'adreca': data['www_street'] if data['www_street'] else '',
            'municipi': data['www_municipi'][1]['name'] if data['www_municipi'] else '',
            'cp': data['www_zip'] if data['www_zip'] else '',
            'provincia': data['www_provincia'][1]['name'] if data['www_provincia'] else '',
            'data_alta': data['date'],
            'data_baixa': data['data_baixa_soci'] if data['data_baixa_soci'] else ''}
        return singles_soci_values

    def get_aportacions_obligatories_values(self, cursor, uid, soci, context=None):
        soci_obj = self.pool.get('somenergia.soci')
        data = soci_obj.read(cursor, uid, soci, ['date', 'data_baixa_soci'])
        inversions = []
        if data['date'] >= context['date_from'] and data['date'] <= context['date_to']:
            inversions.append({
                'data': data['date'],
                'concepte': u'Obligatoria',
                'import': 100
            })
        if data['data_baixa_soci'] and data['data_baixa_soci'] >= context['date_from'] and data['data_baixa_soci'] <= context['date_to']:
            inversions.append({
                'data': data['data_baixa_soci'],
                'concepte': u'Obligatoria',
                'import': -100
            })
        return inversions

    def get_aportacions_voluntaries_values(self, cursor, uid, soci, context=None):
        inv_obj = self.pool.get('generationkwh.investment')
        inv_list = inv_obj.search(cursor, uid, [('member_id', '=', soci),('emission_id','>',1)])
        inversions = []
        for inv in inv_list:
            data = inv_obj.read(cursor, uid, inv, ['purchase_date',
                   'last_effective_date','last_effective_date','nshares',
                   'amortized_amount'])
            if data['purchase_date'] and data['purchase_date'] >= context['date_from'] and data['purchase_date'] <= context['date_to']:
                inversions.append({
                    'data': data['purchase_date'],
                    'concepte': u'Voluntaria',
                    'import': data['nshares']*100,
                    'import_amortitzat':  data['amortized_amount']
                })
            if data['last_effective_date'] and data['last_effective_date'] >= context['date_from'] and data['last_effective_date'] <= context['date_to']:
                inversions.append({
                    'data': data['last_effective_date'],
                    'concepte': u'Voluntaria',
                    'import': data['nshares']*100*-1,
                    'import_amortitzat': data['amortized_amount']*-1
                })
        return inversions

    _columns = {
        'name': fields.char('Nom fitxer', size=32),
        'state': fields.char('State', size=16),
        'date_to': fields.date('Data final',required=True),
        'date_from': fields.date('Data inicial',required=True),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'date_to': lambda *a: str(datetime.today()),
        'date_from': '2010-12-01',
    }

WizardLlibreRegistreSocis()
