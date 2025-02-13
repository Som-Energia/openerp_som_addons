# -*- coding: utf-8 -*-
from osv import fields, osv
import sys
import logging
import datetime
import netsvc
from dateutil.relativedelta import relativedelta
from giscedata_municipal_taxes.taxes.municipal_taxes_invoicing import MunicipalTaxesInvoicingReport

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

        config_obj = self.pool.get('som.municipal.taxes.config')
        wizard = self.browse(cursor, uid, ids, context=context)

        municipi_conf_ids = self.buscar_municipis_remesar(cursor, uid, wizard.quarter, context)
        if not municipi_conf_ids:
            vals = {
                'info': "No hi ha municipis configurats per remesar",
                'state': 'cancel',
            }
            wizard.write(vals, context)
            return True

        res_municipi_ids = [
            m['municipi_id'][0]
            for m in config_obj.read(cursor, uid, municipi_conf_ids, ['municipi_id'])
        ]

        totals_by_city = self.calcul_imports(
            cursor, uid, res_municipi_ids, wizard.year, wizard.quarter, context)
        if not totals_by_city:
            vals = {
                'info': "No hi ha factures dels municipis configurats en el període especificat",
                'state': 'cancel',
            }
            wizard.write(vals, context)
            return True

        order_id, info = self.crear_factures(
            cursor, uid, totals_by_city, wizard.payment_mode.id,
            wizard.account.id, wizard.year, context)

        vals = {
            'info': info,
            'state': 'done',
            'order_id': order_id
        }
        wizard.write(vals, context)
        return order_id

    def buscar_municipis_remesar(self, cursor, uid, quarter, context=None):
        # Buscar els municipis que es remesen
        config_obj = self.pool.get('som.municipal.taxes.config')

        search_values = [('payment_order', '=', True), ('active', '=', True)]
        if quarter == ANUAL_VAL:
            search_values += [('payment', '=', 'year')]
        else:
            search_values += [('payment', '=', 'quarter')]
        if 'from_model' in context:
            search_values += [('id', 'in', context['active_ids'])]

        municipis_conf_ids = config_obj.search(cursor, uid, search_values)

        if not municipis_conf_ids:
            return False

        return municipis_conf_ids

    def calcul_imports(self, cursor, uid, res_municipi_ids, year, quarter, context=None):
        # Calcular els imports
        start_date, end_date = get_dates_from_quarter(year, quarter)
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

        return df_mun # ex totals_by_city

    def crear_factures(self, cursor, uid, totals_by_city, payment_mode_id,
                       account_id, year, context=None):
        config_obj = self.pool.get('som.municipal.taxes.config')
        order_obj = self.pool.get('payment.order')
        currency_obj = self.pool.get('res.currency')
        self.pool.get('payment.line')
        mun_obj = self.pool.get('res.municipi')
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        tax = 1.5
        euro_id = currency_obj.search(cursor, uid, [('code', '=', 'EUR')])[0]
        journal_id = self.pool.get('ir.model.data').get_object_reference(
            cursor, uid, 'som_municipal_taxes', 'municipal_tax_journal')[1]
        # Crear remesa
        order_id = order_obj.create(cursor, uid, dict(
            date_prefered='fixed',
            user_id=uid,
            state='draft',
            mode=payment_mode_id,
            type='payable',
            create_account_moves='direct-payment',
        ))

        invoice_ids = []
        linia_creada = []
        linia_no_creada = []
        for idx, mun in df_gr.iterrows():
            total_tax = mun['TOVP']
            city_name = idx[0]
            city_ine = idx[1]
            quarter_name = idx[3]
            municipi_id = mun_obj.search(cursor, uid, [('ine', '=', ine)])[0]
            origin_name = '{}/{}{}'.format(city_ine, year, quarter_name)
            if invoice_obj.search(cursor, uid, [('origin', '=', origin_name)]):
                linia_no_creada.append(city_name)
                continue

            municipi_id = mun_obj.search(cursor, uid, [('ine', '=', city_ine)])[0]

            # Create account.invoice objects for each city
            invoice_obj = self.pool.get('account.invoice')
            invoice_line_obj = self.pool.get('account.invoice.line')
            # Get partner_address_id from partner_id
            partner_address_id = self.pool.get('res.partner').address_get(
                cursor, uid, [config_data['partner_id'][0]], ['invoice'])['invoice']
            # Create account.invoice objects for each city
            invoice_id = invoice_obj.create(cursor, uid, dict(
                partner_id=config_data['partner_id'][0],
                date_invoice=datetime.datetime.now(),
                account_id=account_id,
                currency_id=euro_id,
                payment_mode_id=payment_mode_id,
                state='draft',
                address_invoice_id=partner_address_id,
                journal_id=journal_id,
                type='in_invoice',
                origin=origin_name,
                reference='',
                origin_date_invoice=self.get_dates_from_quarter(year, quarter_number),
            ))
            invoice_line_obj.create(cursor, uid, dict(
                invoice_id=invoice_id,
                name='Ajuntament de {} taxa 1,5% pel trimestre {}-{}'.format(
                    city_name, year, quarter_name),
                account_id=account_id,
                price_unit=total_tax,
                quantity=1,
                uom_id=1,
                company_currency_id=euro_id,
            ))
            invoice_obj.write(cursor, uid, [invoice_id], {'check_total': total_tax})
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cursor)

            linia_creada.append(city_name)
            invoice_ids.append(invoice_id)

        invoice_obj.afegeix_a_remesa(cursor, uid, invoice_ids, order_id)
        info = "S'ha creat la remesa amb {} línies\n\n".format(len(linia_creada))
        if linia_no_creada:
            info += """Atenció. Els següents ajuntaments no tenen un compte corrent informat
              i per tant no s'ha pogut crear el pagament: {}""".format(", ".join(linia_no_creada))

        return order_id, info

    def get_dates_from_quarter(self, year, quarter):
        if quarter == ANUAL_VAL:
            return datetime.date(year, 1, 1), datetime.date(year, 12, 31)
        else:
            start_date = datetime.date(year, (quarter - 1) * 3 + 1, day=1)
            return start_date.strftime('%Y-%m-%d')

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
