# -*- coding: utf-8 -*-
from osv import fields, osv
import sys
import logging
import datetime
from dateutil.relativedelta import relativedelta
from giscedata_municipal_taxes.taxes.municipal_taxes_invoicing import MunicipalTaxesInvoicingReport

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("wizard.importador.leads.comercials")


ANUAL_VAL = 5


class WizardPresentacioRedSaras(osv.osv_memory):
    _name = "wizard.presentacio.redsaras"

    def enviar_redsaras(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, list):
            ids = ids[0]

        wizard = self.browse(cursor, uid, ids, context=context)

        # Buscar els municipis que es remesen
        config_obj = self.pool.get('som.municipal.taxes.config')
        self.pool.get('res.currency')
        self.pool.get('payment.order')
        self.pool.get('payment.line')
        mun_obj = self.pool.get('res.municipi')

        search_values = [('red_sara', '=', True), ('active', '=', True)]
        if wizard.quarter == ANUAL_VAL:
            search_values += [('payment', '=', 'year')]
        else:
            search_values += [('payment', '=', 'quarter')]
        if 'from_model' in context:
            search_values += [('id', 'in', context['active_ids'])]

        municipis_conf_ids = config_obj.search(cursor, uid, search_values)

        if not municipis_conf_ids:
            vals = {
                'info': "No hi ha municipis configurats per enviar a Red Saras",
                'state': 'cancel',
            }
            wizard.write(vals, context)
            return True

        res_municipi_ids = [
            m['municipi_id'][0]
            for m in config_obj.read(cursor, uid, municipis_conf_ids, ['municipi_id'])
        ]

        # Calcular els imports
        start_date, end_date = get_dates_from_quarter(wizard.year, wizard.quarter)
        tax = 1.5
        polissa_categ_imu_ex_id = (
            self.pool.get('ir.model.data').get_object_reference(
                cursor, uid, 'giscedata_municipal_taxes', 'contract_categ_imu_ex'
            )[1]
        )
        invoiced_states = self.pool.get(
            'giscedata.facturacio.extra').get_states_invoiced(cursor, uid)
        invoiced_states.append('draft')
        taxes_invoicing_report = MunicipalTaxesInvoicingReport(
            cursor, uid, start_date, end_date, False, False, False,
            polissa_categ_imu_ex_id, False, invoiced_states,
            context=context
        )
        totals_by_city = taxes_invoicing_report.get_totals_by_city(res_municipi_ids)
        if not totals_by_city:
            vals = {
                'info': "No hi ha factures dels municipis configurats en el període especificat",
                'state': 'cancel',
            }
            wizard.write(vals, context)
            return True

        # Encuar per a RedSaras

        for city in totals_by_city:
            round(city[4] - city[3] * (tax / 100.0), 2)
            municipi_id = mun_obj.search(cursor, uid, [('ine', '=', city[5])])[0]
            config_id = config_obj.search(cursor, uid, [('municipi_id', '=', municipi_id)])[0]
            config_data = config_obj.read(cursor, uid, config_id, ['partner_id'])
            dict(self._columns['quarter'].selection)[int(city[2])]
            vals = {
                'partner_id': config_data['partner_id'][0],
            }

        info = "S'ha encuat la presentació a Red Saras de {} ajuntaments\n\n".format(
            len(totals_by_city))

        vals = {
            'info': info,
            'state': 'done',
        }
        wizard.write(vals, context)
        return True

    def show_payment_order(self, cursor, uid, ids, context):
        wizard = self.browse(cursor, uid, ids[0], context)
        return True
        return {
            'domain': "[('id','=', %s)]" % str(wizard.order_id),
            'name': 'Ordre de pagament',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'payment.order',
            'type': 'ir.actions.act_window',
        }

    _columns = {
        'state': fields.char('Estat', size=16, required=True),
        "info": fields.text("info"),
        "year": fields.integer("Any", required=True),
        "quarter": fields.selection(
            [(1, '1T'), (2, '2T'), (3, '3T'), (4, '4T'), (ANUAL_VAL, 'Anual')],
            'Trimestre', required=True
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'year': lambda *a: datetime.datetime.today().year,
    }


def get_dates_from_quarter(year, quarter):
    if quarter == ANUAL_VAL:
        return datetime.date(year, 1, 1), datetime.date(year, 12, 31)
    else:
        start_date = datetime.date(year, (quarter - 1) * 3 + 1, day=1)
        return (
            start_date,
            start_date + relativedelta(months=3) - datetime.timedelta(days=1)
        )


WizardPresentacioRedSaras()
