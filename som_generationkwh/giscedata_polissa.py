# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from osv import osv, fields
from osv.expression import OOQuery
from collections import defaultdict

class GiscedataPolissaTarifaPeriodes(osv.osv):
    """Periodes de les Tarifes."""
    _name = 'giscedata.polissa.tarifa.periodes'
    _inherit = 'giscedata.polissa.tarifa.periodes'

    _columns = {
        'product_gkwh_id': fields.many2one(
            'product.product', 'Generation kWh', ondelete='restrict'
        ),
    }

GiscedataPolissaTarifaPeriodes()


class GiscedataPolissa(osv.osv):

    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def get_polisses_from_assignments(self, cursor, uid, ids, context=None):
        """ ids és la llista de 'generationkwh.assignment' que han sigut modificats
        retorna una llista de ids de 'giscedata.polissa' per les quals cal modificar el càlcul"""

        assig_obj = self.pool.get('generationkwh.assignment')

        pol_ids = assig_obj.read(cursor, uid, ids, ['contract_id'])
        return [p['contract_id'][0] for p in pol_ids]

    def _ff_get_assignacio_gkwh(self, cursor, uid, ids, field_name, arg,
                              context=None):
        if not context:
            context = {}
        assig_obj = self.pool.get('generationkwh.assignment')
        res = dict.fromkeys(ids, False)

        for _id in ids:
            search_params = [('contract_id','=', _id)]
            assigment_id = assig_obj.search(cursor, uid, search_params, limit=1)
            res[_id] = len(assigment_id) > 0

        return res

    def get_generationkwh_use(self, cursor, uid, pol_id, date_start, date_end, context=None):
        """
            Returns a dict with invoice date as first key, period as second key, and kWh as value:
            In exemple: {
                '2026-04-11': {
                    'P1': 10,
                    'P2': 8,
                    'P3': 2,
                },
                '2026-05-12': {
                    'P1': 12,
                    'P2': 6,
                    'P3': 1,
                },
            }
        """
        GenerationkWhInvoiceLineOwner = self.pool.get('generationkwh.invoice.line.owner')
        q = OOQuery(GenerationkWhInvoiceLineOwner, cursor, uid)

        date_domain = [
            ('factura_id.invoice_id.date_invoice', '>=', date_start),
            ('factura_id.invoice_id.date_invoice', '<=', date_end)
        ]

        sql = q.select(['id']).where([('factura_id.polissa_id.id', '=', pol_id)] + date_domain)
        cursor.execute(*sql)
        res = cursor.fetchall()
        generation_line_ids = [line[0] for line in res]

        response = defaultdict(lambda: defaultdict(int))
        for gkwh_line in GenerationkWhInvoiceLineOwner.browse(cursor, uid, generation_line_ids, context=context):
            invoice = gkwh_line.factura_id
            line = gkwh_line.factura_line_id
            date_invoice = invoice.invoice_id.date_invoice
            multiplier = 1 if invoice.type in ('out_invoice', 'in_refund') else -1
            product_name = str(line.product_id.name)
            response[str(date_invoice)][product_name] += (line.quantity * multiplier)

        # clean defaultdict for serialization
        response = {k: dict(v) for k, v in response.items()}
        return response

    def generationkwh_anual_estimation(self, cursor, uid, pol_id, date_end=None, context=None):
        """
            Calculates generationkwh anual estimation:
                - If there are 12 months of data, is just the sum of every period
                - If there are some data, is ponerated to 12 months with a rule of 3
                - If there are no data, returns False
            It returns a tuple with the estimation and a string with the type of estimation:
            'full_data', 'partial_data' or 'no_data'
        """
        if not date_end:
            date_end = str(date.today())

        date_end_dt = datetime.strptime(date_end, '%Y-%m-%d').date()
        date_start_dt = date_end_dt - relativedelta(years=1)
        date_start = str(date_start_dt)

        use_data = self.get_generationkwh_use(
            cursor, uid, pol_id, date_start, date_end, context=context)

        if not use_data:
            return False, 'no_data'

        period_sums = {}
        for _, periods in use_data.items():
            for p, kwh in periods.items():
                period_sums[p] = period_sums.get(p, 0) + kwh

        num_invoices = len(use_data)
        factor = 12.0 / num_invoices
        res = {p: int(round(kwh * factor)) for p, kwh in period_sums.items()}

        return res, 'full_data' if num_invoices >= 12 else 'partial_data'

    _columns = {
        'te_assignacio_gkwh': fields.function(
            _ff_get_assignacio_gkwh, method=True, type='boolean',
            string='Té assignacions GWKH', readonly=True, help="El contracte té assignacions de GKWH, sense tenir en compte la prioritat ni data fi.",
            store={'generationkwh.assignment': (
                get_polisses_from_assignments,
                ['contract_id'],
                10)
            }),
    }


GiscedataPolissa()
