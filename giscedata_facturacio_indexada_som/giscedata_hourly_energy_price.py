# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv
from .tarifes import TARIFFS_FACT


class GiscedataNextDaysEnergyPrice(osv.osv):
    _inherit = 'giscedata.next.days.energy.price'

    def get_tarifa_class(self, cursor, uid, tarifa_name, context=None):
        return TARIFFS_FACT[tarifa_name]

    def get_versions(self, cursor, uid, tarifa_id, data_inici, geom_zone, context=None):
        if context is None:
            context = {}

        pricelist_obj = self.pool.get('product.pricelist')
        imd_obj = self.pool.get('ir.model.data')

        res = super(GiscedataNextDaysEnergyPrice, self).get_versions(
            cursor, uid, tarifa_id, data_inici, geom_zone, context=context
        )

        llista_preu_id = self.get_pricelist_id(cursor, uid, geom_zone, tarifa_id, context=context)
        if not llista_preu_id:
            raise osv.except_osv('Error', 'No s\'ha indicat cap llista de preus.')

        # Afegim els productes nous
        gdos_som = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_gdos_som'
        )[1]
        factor_dsv = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_factor_dsv_som'
        )[1]
        pauvi = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_auvi_som'
        )[1]

        ctx = context.copy()
        ctx.update({'component_qh': True})
        for date_version in res:
            ctx['date'] = date_version
            res[date_version]['gdos'] = pricelist_obj.price_get(
                cursor, uid, [llista_preu_id], gdos_som, 1, context=ctx
            )[llista_preu_id]
            res[date_version]['factor_dsv'] = pricelist_obj.price_get(
                cursor, uid, [llista_preu_id], factor_dsv, 1, context=ctx
            )[llista_preu_id]
            res[date_version]['pauvi'] = pricelist_obj.price_get(
                cursor, uid, [llista_preu_id], pauvi, 1, context=ctx
            )[llista_preu_id]
            # res[date_version]['bs3qh'] = reganecu_obj.get_reganecu_components_between_dates(
            #     cursor, uid, data_inici, data_final, 'BS3', context=ctx
            # )
            # res[date_version]['rad3qh'] = reganecu_obj.get_reganecu_components_between_dates(
            #     cursor, uid, data_inici, data_final, 'RAD3', context=ctx
            # )

        return res


GiscedataNextDaysEnergyPrice()
