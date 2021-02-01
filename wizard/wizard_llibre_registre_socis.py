# -*- coding: utf-8 -*-
import tools
from osv import osv, fields
from datetime import datetime


class WizardLlibreRegistreSocis(osv.osv_memory):
    """Assistent per generar registre de socis"""

    _name = 'wizard.llibre.registre.socis'


    def print_report(self, cursor, uid, ids, context=None):
	wiz = self.browse(cursor, uid, ids[0])
	dades = self.get_report_data(cursor, uid, ids)
	if not context:
	    context = {}
	return {
	    'type': 'ir.actions.report.xml',
	    'model': 'somenergia.soci',
	    'report_name': 'som.polissa.soci.report_llibre_registre_socis',
	    'report_webkit': "'som_polissa_soci/report/report_llibre_registre_socis.mako'",
	    'webkit_header': 'report_sense_fons',
	    'groups_id': [],
	    'multi': '0',
	    'auto': '0',
	    'header': '0',
	    'report_rml': 'False',
	    'datas': {
		'dades': dades,
	    },
	}


    def get_report_data(self, cursor, uid, ids, context=None):
        #wizard = self.browse(cursor, uid, ids[0], context)
        soci_obj = self.pool.get('somenergia.soci')
        socis = soci_obj.search(cursor, uid, [('active','=',True)])
        values = {}
        for soci in socis[:2]:
            header = self.get_soci_values(cursor, uid, soci)
            apos = self.get_aportacions_obligatories_values(cursor, uid, soci)
            apo_vol = self.get_aportacions_voluntaries_values(cursor, uid, soci)
            quadre_moviments = apos + apo_vol#sorted(apos.items(), key=lambda item: item[1]['data_compra'])
            header.update({'inversions': quadre_moviments})
            values[str(soci)] = header

	return values

    def get_soci_values(self, cursor, uid, soci, context=None):
        #Obtenir dades del partner
        soci_obj = self.pool.get('somenergia.soci')
        data = soci_obj.read(cursor, uid, soci)
        singles_soci_values = {
            'tipus': 'Consumidor',
            'num_soci': data['ref'],
            'nom': data['name'],
            'dni': data['vat'][2:],
            'email': data['www_email'],
            'adreca': data['www_street'],
            'municipi': False if not data['www_municipi'] else data['www_municipi'][1]['name'],
            'cp': data['www_zip'],
            'provincia': data['www_provincia'][1]['name'] if data['www_provincia'] else False,
            #'provincia': data['www_provincia'][1]['name'],
            'data_alta': data['date'],
            'data_baixa': data['data_baixa_soci']}
        return singles_soci_values

    def get_aportacions_obligatories_values(self, cursor, uid, soci):
        #Obtenir aportació de 100€ (agafar data d'alta com a data d'aportació)
        soci_obj = self.pool.get('somenergia.soci')
        data = soci_obj.read(cursor, uid, soci)
        inversions = []
        inversions.append({
            'data_compra': data['date'],
            'concepte': u'Aportación obligatoria',
            'import': 100
        })
        if data['data_baixa_soci']:
            inversions.append({
                'data_compra': data['date_baixa_soci'],
                'concepte': u'Aportación obligatoria',
                'import': -100
            })
        return inversions

    def get_aportacions_voluntaries_values(self, cursor, uid, soci):
        #Obtenir aportacions voluntàries
        inv_obj = self.pool.get('generationkwh.investment')
        inv_list = inv_obj.search(cursor, uid, [('member_id', '=', soci),('emission_id','>',1)])
        inversions = []
        for inv in inv_list:
            data = inv_obj.read(cursor, uid, inv)
            if data['purchase_date']:
                if data['last_effective_date']:
                    inversions.append({
                        'data_compra': data['purchase_date'],
                        'data_venda': data['last_effective_date'],
                        'concepte': u'Aportación voluntaria',
                        'import': data['nshares']*100*-1,
                        'import_amortitzat': data['amortized_amount']*-1
                })
                inversions.append({
                    'data_compra': data['purchase_date'],
                    'data_venda': data['last_effective_date'],
                    'concepte': u'Aportación voluntaria',
                    'import': data['nshares']*100,
                    'import_amortitzat':  data['amortized_amount']
                })
        return inversions

    _columns = {
        'name': fields.char('Nom fitxer', size=32),
        'state': fields.char('State', size=16),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }

WizardLlibreRegistreSocis()