# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _
from tools import config

from libfacturacioatr.pool.tarifes import *
from libfacturacioatr.pool import REECoeficientsNotFound
from enerdata.datetime.holidays import get_holidays
from datetime import datetime

import logging

logger = logging.getLogger('openerp.' + __name__)


class GiscedataNextDaysEnergyPrice(osv.osv):
    _inherit = 'giscedata.next.days.energy.price'

    def get_versions(self, cursor, uid, tarifa, data_inici, geom_zone, context=None):
        if context is None:
            context = {}

        res = super(GiscedataNextDaysEnergyPrice, self).get_versions(cursor, uid, tarifa, data_inici, geom_zone, context=context)

        config_obj = self.pool.get('res.config')
        imd_obj = self.pool.get('ir.model.data')
        pricelist_obj = self.pool.get('product.pricelist')

        # Productes
        pl_config_data = eval(config_obj.get(cursor, uid, 'tarifa_acces_to_pl_mapeig', '{}'))
        pricelist = pl_config_data[geom_zone].get(tarifa['name'])

        gdos_item = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_gdos_som'
        )[1]
        dsv_item = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_factor_dsv_som'
        )[1]

        # Preus
        gdos = pricelist_obj.price_get(
            cursor, uid, [pricelist], gdos_item, 1, context=context)[pricelist]
        factor_dsv = pricelist_obj.price_get(
            cursor, uid, [pricelist], dsv_item, 1, context=context)[pricelist]

        # Actualitzar res
        res[data_inici].update({'factor_dsv': factor_dsv, 'gdos': gdos})

        return res

GiscedataNextDaysEnergyPrice()
