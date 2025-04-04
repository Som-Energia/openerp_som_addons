# -*- coding: utf-8 -*-
from osv import fields, osv
import sys
import logging
import datetime
from dateutil.relativedelta import relativedelta
from giscedata_municipal_taxes.taxes.municipal_taxes_invoicing import MunicipalTaxesInvoicingReport
from psycopg2.errors import UniqueViolation

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("wizard.importador.leads.comercials")


ANUAL_VAL = 5


class WizardCreacioRemesaPagamentTaxes(osv.osv_memory):
    _name = "wizard.creacio.remesa.pagament.taxes"

    def create_remesa_pagaments(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, list):
            ids = ids[0]

        wizard = self.browse(cursor, uid, ids, context=context)

        # Buscar els municipis que es remesen
        config_obj = self.pool.get('som.municipal.taxes.config')
        currency_obj = self.pool.get('res.currency')
        order_obj = self.pool.get('payment.order')
        line_obj = self.pool.get('payment.line')
        mun_obj = self.pool.get('res.municipi')

        search_values = [('payment_order', '=', True), ('active', '=', True)]
        if wizard.quarter == ANUAL_VAL:
            search_values += [('payment', '=', 'year')]
        else:
            search_values += [('payment', '=', 'quarter')]
        if 'from_model' in context:
            search_values += [('id', 'in', context['active_ids'])]

        municipis_conf_ids = config_obj.search(cursor, uid, search_values)

        if not municipis_conf_ids:
            vals = {
                'info': "No hi ha municipis configurats per remesar",
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
        polissa_categ_imu_ex_id = (
            self.pool.get('ir.model.data').get_object_reference(
                cursor, uid, 'giscedata_municipal_taxes', 'contract_categ_imu_ex'
            )[1]
        )
        invoiced_states = self.pool.get(
            'giscedata.facturacio.extra').get_states_invoiced(cursor, uid)
        taxes_invoicing_report = MunicipalTaxesInvoicingReport(
            cursor, uid, start_date, end_date, False, False, 'tri', False,
            polissa_categ_imu_ex_id, False, invoiced_states,
            context=context
        )
        df_mun, df_gr, df_out, df_in, col_gr, col_mun = taxes_invoicing_report.build_dataframe_taxes_detallat(  # noqa: E501
            res_municipi_ids, context)
        if not col_mun:
            vals = {
                'info': "No hi ha factures dels municipis configurats en el període especificat",
                'state': 'cancel',
            }
            wizard.write(vals, context)
            return True

        # Crear remesa
        order_id = order_obj.create(cursor, uid, dict(
            date_prefered='fixed',
            user_id=uid,
            state='draft',
            mode=wizard.payment_mode.id,
            type='payable',
            create_account_moves='direct-payment',
        ))
        linia_creada = []
        linia_no_creada = []
        for idx, mun in df_gr.iterrows():
            total_tax = mun['TOVP']
            municipi_id = mun_obj.search(cursor, uid, [('ine', '=', idx[1])])[0]
            config_id = config_obj.search(cursor, uid, [('municipi_id', '=', municipi_id)])[0]
            config_data = config_obj.read(cursor, uid, config_id, ['partner_id', 'bank_id'])
            if not config_data['bank_id']:
                linia_no_creada.append(config_data['name'])
                continue

            account_id = wizard.account.id

            # Crear les línies
            euro_id = currency_obj.search(cursor, uid, [('code', '=', 'EUR')])[0]
            quarter_name = idx[3]
            vals = {
                'name': 'Ajuntament de {} taxa 1,5% pel trimestre {}-{}'.format(
                    idx[0], wizard.year, quarter_name),
                'order_id': order_id,
                'currency': euro_id,
                'partner_id': config_data['partner_id'][0],
                'company_currency': euro_id,
                'bank_id': config_data['bank_id'][0],
                'state': 'normal',
                'amount_currency': -1 * total_tax,
                'account_id': account_id,
                'communication': 'Ajuntament de {} taxa 1,5%'.format(idx[0]),
                'comm_text': 'Ajuntament de {} taxa 1,5%'.format(idx[0]),
            }
            try:
                line_obj.create(cursor, uid, vals)
                linia_creada.append(idx[0])
            except UniqueViolation:
                raise osv.except_osv(
                    ('Error!'), (
                        "Ja s'ha pagat el trimestre {}-{} per a l'ajuntament {}".format(
                            wizard.year, quarter_name, idx[0])
                    )
                )

        info = "S'ha creat la remesa amb {} línies\n\n".format(len(linia_creada))
        if linia_no_creada:
            info += """Atenció. Els següents ajuntaments no tenen un compte corrent informat
              i per tant no s'ha pogut crear el pagament: {}""".format(", ".join(linia_no_creada))

        vals = {
            'info': info,
            'state': 'done',
            'order_id': order_id
        }
        wizard.write(vals, context)
        return order_id

    def show_payment_order(self, cursor, uid, ids, context):
        wizard = self.browse(cursor, uid, ids[0], context)
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
        "account": fields.many2one(
            "account.account", "Compte comptable", help="On comptabilitzar les taxes (grup 4751)"),
        "payment_mode": fields.many2one("payment.mode", "Mode de pagament"),
        "info": fields.text("info"),
        "year": fields.integer("Any", required=True),
        "quarter": fields.selection(
            [(1, '1T'), (2, '2T'), (3, '3T'), (4, '4T'), (ANUAL_VAL, 'Anual')],
            'Trimestre', required=True
        ),
        'order_id': fields.integer("id remesa"),
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


WizardCreacioRemesaPagamentTaxes()
