# -*- coding: utf-8 -*-
from osv import osv, fields
from osv.osv import except_osv
from tools.translate import _

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
