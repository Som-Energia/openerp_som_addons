# -*- coding: utf-8 -*-
from osv import fields, osv
import sys
import logging
from giscedata_municipal_taxes.taxes.municipal_taxes_invoicing import MunicipalTaxesInvoicingReport

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("wizard.importador.leads.comercials")


class WizardCreacioRemesaPagamentTaxes(osv.osv_memory):
    _name = "wizard.creacio.remesa.pagament.taxes"

    def create_remesa_pagaments(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, list):
            ids = ids[0]

        res = {}
        wiz = self.browse(cursor, uid, ids, context=context)

        # Buscar els municipis que es remesen
        config_obj = self.pool.get('som.municipal.taxes.config')
        currency_obj = self.pool.get('res.currency')
        order_obj = self.pool.get('payment.order')
        line_obj = self.pool.get('payment.line')

        municipis = config_obj.search(cursor, uid, [('type', '=', 'remesa')])

        if not municipis:
            vals = {
                'info': "No hi ha municipis configurats per remesar",
                'state': 'done',
            }
            self.write(cursor, uid, [ids], vals, context)
            return res

        res_municipi_ids = config_obj.read(municipis, ['municipi_id'])

        # Calcular els imports
        start_date = '2024-01-01'
        end_date = '2024-03-31'
        tax = 1.5
        polissa_categ_imu_ex_id = (
            self.pool.get('ir.model.data').get_object_reference(
                cursor, uid, 'giscedata_municipal_taxes', 'contract_categ_imu_ex'
            )[1]
        )
        invoiced_states = self.pool.get(
            'giscedata.facturacio.extra').get_states_invoiced(cursor, uid)
        taxes_invoicing_report = MunicipalTaxesInvoicingReport(
            cursor, uid, start_date, end_date, False, False, False,
            polissa_categ_imu_ex_id, False, invoiced_states,
            context=context
        )
        totals_by_city = taxes_invoicing_report.get_totals_by_city(res_municipi_ids)

        # Crear remesa
        # order_id = 11603
        order = order_obj.create(dict(
            date_prefered='fixed',
            user_id=uid,
            state='draft',
            mode=wiz.payment_mode,
            type='payable',
            create_account_moves='direct-payment',
        ))
        order_id = order.id

        for city in totals_by_city:
            total_tax = round(city[4] - city[3] * (tax / 100.0), 2)

            # TODO obtenir municip a traves d'INE city[5] i després partner i bank
            partner_id = 54047
            bank_id = 77705

            # account_id = 166127
            account_id = wiz.account

            # Crear les línies
            euro_id = currency_obj.search([('code', '=', 'EUR')])
            vals = {
                'name': 'Ajuntament de {} taxa 1,5%'.format(city[0]),
                'order_id': order_id,
                'currency': euro_id,
                'partner_id': partner_id,
                'company_currency': euro_id,
                'bank_id': bank_id,
                'state': 'normal',
                'amount_currency': -1 * total_tax,
                'account_id': account_id,
                'communication': 'Ajuntament de {} taxa 1,5%'.format(city[0]),
                'comm_text': 'Ajuntament de {} taxa 1,5%'.format(city[0]),
            }
            line_obj.create(cursor, uid, vals)

        vals = {
            'info': "S'ha creat la remesa amb {} línies".format(len(totals_by_city)),
            'state': 'done',
        }
        self.write(cursor, uid, [ids], vals, context)
        return res

    _columns = {
        'state': fields.char('Estat', size=16, required=True),
        "account": fields.many2one(
            "account.account", "Compte comptable", help="On comptabilitzar les taxes (grup 4751)"),
        "payment_mode": fields.many2one("payment.mode", "Mode de pagament"),
        "info": fields.char('Info', size=124),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }


WizardCreacioRemesaPagamentTaxes()
