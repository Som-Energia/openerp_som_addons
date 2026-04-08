# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv


# TODO: This must be in the generationkwh module, but we have a mess in dependencies
class GiscedataPolissaTarifa(osv.osv):
    """Tarifa d'accés de les pòlisses."""
    _name = 'giscedata.polissa.tarifa'
    _inherit = 'giscedata.polissa.tarifa'

    def get_periodes_producte(self, cursor, uid, tarifa_id, tipus, context=None):
        if tipus != 'gkwh':
            return super(GiscedataPolissaTarifa, self).get_periodes_producte(
                cursor, uid, tarifa_id, tipus, context=context
            )

        productes = {}
        if isinstance(tarifa_id, list) or isinstance(tarifa_id, tuple):
            tarifa_id = tarifa_id[0]
        tarifa = self.browse(cursor, uid, tarifa_id, context)
        for periode in tarifa.periodes:
            if periode.product_gkwh_id:
                productes[periode.name] = periode.product_gkwh_id.id

        return productes


GiscedataPolissaTarifa()
