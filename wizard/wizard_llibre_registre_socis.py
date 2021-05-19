# -*- coding: utf-8 -*-
import base64
from c2c_webkit_report import webkit_report
from datetime import datetime
from oorq.decorators import job
from osv import osv, fields
from report import report_sxw
import tools


class WizardLlibreRegistreSocis(osv.osv_memory):
    """Assistent per generar registre de socis"""

    _name = 'wizard.llibre.registre.socis'

    def generate_report(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0])
        context['date_from'] = wiz.date_from
        context['date_to'] = wiz.date_to
        self.generate_one_report(cursor, uid, ids, context)
        return {}


    @job(queue="print_report", timeout=3000)
    def generate_one_report(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0])
        dades = self.get_report_data(cursor, uid, ids, context)
        header = {}
        header['date_from'] = context['date_from']
        header['date_to'] = context['date_to']

        report_printer = webkit_report.WebKitParser(
            'report.somenergia.soci.report_llibre_registre_socis',
            'somenergia.soci',
            'som_generationkwh/report/report_llibre_registre_socis.mako',
            parser=report_sxw.rml_parse
        )

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

        f = open("/tmp/reports/llibre_registre_socis_" + str(header['date_to'][:4]) + ".pdf", 'wb+' )
        try:
            bits = base64.b64decode(base64.b64encode(document_binary[0]))
            f.write(bits)
        finally:
            f.close()

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
        if data['date'] >= context['date_from'] and data['date'] <= context['date_to'] and data['data_baixa_soci']:
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
