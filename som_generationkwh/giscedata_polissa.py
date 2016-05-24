# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields

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
