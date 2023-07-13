# -*- coding: utf-8 -*-
from osv import osv, fields
from osv.osv import except_osv
from tools.translate import _
from addons.giscedata_facturacio.giscedata_polissa import _get_polissa_from_invoice

import datetime

class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp teoric_maximum_consume_gc.
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def _ff_observations_first_line(self, cursor, uid, ids, args, fields, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, False)
        for pol_id in ids:
            observacions = self.read(cursor, uid, pol_id, ['observacions_comptables'], context=context)[
                'observacions_comptables']
            if observacions:
                res[pol_id] = observacions.splitlines()[0]

        return res

    def _ff_mesos_factura_mes_antiga_impagada(self, cursor, uid, ids, args, fields, context=None):
        if context is None:
            context = {}
        fact_o = self.pool.get("giscedata.facturacio.factura")
        res = dict.fromkeys(ids, False)
        for pol_id in ids:
            numero_mesos_antiguitat = 0  # Si no trobem cap factura enviem un 0
            # Agafem la factura mes antiga que estigui impagada
            facturas = fact_o.q(cursor, uid).read(['date_invoice'], only_active=False, limit=1, order_by=('date_invoice.asc', )).where([
                ('polissa_id', '=', pol_id),
                ('type', '=', 'out_invoice'),
                ('state', '=', 'open'),
                ('invoice_id.pending_state.weight', '>', 0)
            ])

            if facturas:
                factura = facturas[0]
                data_factura = factura['date_invoice']
                data_avui = datetime.datetime.now()
                data_factura = datetime.datetime.strptime(data_factura, "%Y-%m-%d")
                delta = data_avui - data_factura
                numero_mesos_antiguitat = delta.days/30
            res[pol_id] = numero_mesos_antiguitat

        return res

    def change_state(self, cursor, uid, ids, context=None):
        values = self.read(cursor, uid, ids, ['invoice_id'], context=context)
        invoice_ids = [value['invoice_id'][0] for value in values]
        return _get_polissa_from_invoice(self, cursor, uid, invoice_ids, context=context)

    def _ff_data_ultima_factura(self, cursor, uid, ids, args, fields, context=None):
        if context is None:
            context = {}
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        res = dict.fromkeys(ids, False)
        for pol_id in ids:
            fact_date = fact_obj.q(cursor, uid).read(['date_invoice'],
                                                     order_by=['invoice_id.date_invoice.desc'],
                                                     limit=1).where([('polissa_id', '=', pol_id)])
            if len(fact_date):
                res[pol_id] = fact_date[0].get('date_invoice')

        return res

    _columns = {
        'teoric_maximum_consume_gc': fields.float(
            digits=(8,2),
            string='Teoric maximum consume Grans Contractes',
            help=u"Màxim consum mensual teòric d'un contracte amb categoria Gran Consum associat a la validació SF03."),
        'observacions_comptables': fields.text('Accounting Observations'),
        'resum_observacions_comptables': fields.function(_ff_observations_first_line, type='text', method=True, string=_('Accounting observations')),
        'mesos_factura_mes_antiga_impagada': fields.function(
            _ff_mesos_factura_mes_antiga_impagada,
            type='integer',
            method=True,
            string=_('Months old of oldest unpayed invoice'),
            store={
                'account.invoice': (_get_polissa_from_invoice, ['state', 'residual', 'pending_state', 'date_invoice'], 20),
                'account.invoice.pending.history': (change_state, ['change_date'], 10),
                'giscedata.polissa': (lambda self, cursor, uid, ids, c=None: ids, ['potencies_periode'], 20)
                }
            ),
        'data_ultima_factura': fields.function(_ff_data_ultima_factura, type='date', method=True, string=_('Last invoice date'))

    }

GiscedataPolissa()

class GiscedataPolissaModcontractual(osv.osv):
    """Modificació Contractual d'una Pòlissa."""
    _name = 'giscedata.polissa.modcontractual'
    _inherit = 'giscedata.polissa.modcontractual'

    _columns = {
        'teoric_maximum_consume_gc': fields.float(digits=(8,2), string='Teoric maximum consume Grans Contractes')
    }


GiscedataPolissaModcontractual()
