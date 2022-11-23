# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import base64

import csv


class WizardInformeDadesDesagregades(osv.osv_memory):
    """
    Wizard per llençar l'informe dades desagregades de la factura
    """
    _name = "wizard.informe.dades_desagregades"

    def create_csv(items, from_date, to_date):
        file_name = 'Informe_factures_dades_desagregades_{}_{}.csv'.format(
            from_date, to_date)
        with open(file_name, 'w') as output_file:
            for e in items.values():
                for key, value in e.items():
                    if isinstance(value, float):
                        e[key] = str(value).replace('.', ',')

            dict_writer = csv.DictWriter(
                output_file, items.keys(), delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(items.values())

        mfile = base64.b64encode(output_file.getvalue())
        output_file.close()
        return mfile

    def get_contract_ids(self, contracts):
        pol_obj = self.pool.get('giscedata.polissa')

        # only 3.0TD and 6.xTD
        search_params = [('tarifa.codi_ocsum', 'in', [
                          '019', '020', '021', '022', '023'])]
        if contracts:
            search_params.append(('id', 'in', contracts))

        return pol_obj.search(search_params)

    def find_invoices(self, pol_ids, from_date, to_date):
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')

        items = {}

        for pol_id in pol_ids:
            pol = pol_obj.browse(pol_id)
            subitem = OrderedDict([('Contracte', pol.name), ('Tarifa Comercialitzadora', pol.llista_preu.name if pol.llista_preu else ''), ('Indexada', 'Indexada' if pol.llista_preu and 'indexada' in pol.llista_preu.name.lower(
            ) else 'No'), ('Energia activa', 0), ('MAG', 0), ('Penalització reactiva', 0), ('Potència', 0), ('Excés potència', 0), ('Excedents', 0), ('Lloguer comptador', 0), ('IVA', 0), ('IGIC', 0), ('IESE', 0), ('Altres', 0), ('TOTAL', 0)])
            items[pol_id] = subitem

        facts = fact_obj.browse([('polissa_id', 'in', pol_ids), ('data_inici', '>=', from_date), ('data_final', '<=', to_date),
                                ('type', 'in', ['out_invoice', 'out_refund']), ('state', '!=', 'draft')])

        for fact in facts:
            pol_item = items[fact.polissa_id.id]

            factor = 1.0 if fact.type == 'out_invoice' else -1.0
            for line in fact.linies_energia:
                if 'topall del gas' in line.name:
                    pol_item['MAG'] += line.price_subtotal * factor
                else:
                    pol_item['Energia activa'] += line.price_subtotal * factor
            pol_item['Penalització reactiva'] += fact.total_reactiva * factor
            pol_item['Potència'] += fact.total_potencia * factor
            pol_item['Excés potència'] += fact.total_exces_potencia * factor
            pol_item['Excedents'] += fact.total_generacio * factor
            pol_item['Lloguer comptador'] += fact.total_lloguers * factor
            for tax_line in fact.tax_line:
                if 'IVA' in tax_line.name:
                    pol_item['IVA'] += tax_line.amount * factor
                elif 'IGIC' in tax_line.name:
                    pol_item['IGIC'] += tax_line.amount * factor
                else:
                    pol_item['IESE'] += tax_line.amount * factor
            pol_item['Altres'] += fact.total_altres * factor
            pol_item['TOTAL'] += fact.amount_total * factor

            item_values = pol_item.items()
            for key, value in item_values:
                if isinstance(value, float):
                    pol_item[key] = round(value, 2)

            items[fact.polissa_id.id] = pol_item

            return items

    def action_crear_informe(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]

        wiz = self.browse(cursor, uid, ids[0])
        wiz.write({'state': 'create'})

        to_date = datetime.strftime(self.to_date, '%Y-%m-%d')
        from_date = datetime.strftime(self.from_date, '%Y-%m-%d')
        contracts = list(set(map(str.strip, str(self.contracts).split(','))))

        pol_ids = self.get_contract_ids(contracts)

        items = self.find_invoices(pol_ids, from_date, to_date)

        output_file = self.create_csv(items, from_date, to_date)

        wiz.write({'file': output_file})

    def set_to_date(self, cursor, uid, context=None):
        day_initial_date = int(self.start_date.strftime("%d"))
        self.to_date = self.start_date - timedelta(days=day_initial_date)

    def set_from_date(self, cursor, uid, context=None):
        self.from_date = self.to_date - \
            relativedelta(months=12) + timedelta(days=1)

    def onchange_start_date(self, cursor, uid, start_date):
        return {'value': {'name': 1}}

    _columns = {
        'state': fields.char('Estat', size=16, required=True),
        'start_date': fields.date('Data inici càlcul', required=True),
        'from_date': fields.date(
            'Data inici inf.', required=True, readonly=True),
        'to_date': fields.date(
            'Data fi inf.', required=True, readonly=True),
        'contracts': fields.char('Contractes', size=256, required=False),
        'file': fields.binary('Informe dades desagregades CSV'),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'start_date': datetime.today(),
        'from_date': set_from_date,
        'to_date': set_to_date,
    }


WizardInformeDadesDesagregades()
