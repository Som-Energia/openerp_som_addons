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
        if context is None:
            context = {}
        factura_obj = self.pool.get('giscedata.facturacio.factura')
        bat_polissa_obj = self.pool.get("giscedata.bateria.virtual.polissa")
        dmn = [
            ('polissa_id', '=', ids[0]),
            ('es_origen', '=', True)
        ]
        bat_id = bat_polissa_obj.q(cursor, uid).read(
            ['bateria_id']
        ).where(dmn)
        bat_id = bat_id[0]['bateria_id']
        data_inici_bat_pol = bat_polissa_obj.read(cursor, uid, bat_id, ['data_inici'], context=context)['data_inici']

        factura_ids = factura_obj.search(cursor, uid, [
            ('polissa_id', '=', ids[0]),
            ('date_invoice', '>=', data_inici),
            ('data_inici', '>=', data_inici_bat_pol),
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