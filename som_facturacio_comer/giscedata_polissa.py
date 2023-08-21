# -*- coding: utf-8 -*-
from osv import osv, fields
from osv.osv import except_osv

import datetime

class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp teoric_maximum_consume_gc.
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def search_factura(self, cursor, uid, ids, data_inici, data_final, context=None):
        factura_obj = self.pool.get('giscedata.facturacio.factura')
        factura_ids = factura_obj.search(cursor, uid, [
            ('polissa_id', '=', ids[0]),
            ('data_inici', '>=', data_inici),
            ('state', 'in', ('paid', 'open')),
            ('type', 'in', ('out_invoice', 'out_refund')),
            '|',
            ('data_final', '<=', data_final),
            ('data_final', '=', False)
        ], context=context
                                         )
        return factura_ids

    _columns = {
        'teoric_maximum_consume_gc': fields.float(
            digits=(8,2),
            string='Teoric maximum consume Grans Contractes',
            help=u"Màxim consum mensual teòric d'un contracte amb categoria Gran Consum associat a la validació SF03.")
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