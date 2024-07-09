# -*- coding: utf-8 -*-
from osv import osv
from .tarifes import TARIFFS_FACT


class GiscedataFacturacioFacturador(osv.osv):
    _name = 'giscedata.facturacio.facturador'
    _inherit = 'giscedata.facturacio.facturador'

    def get_tarifa_class(self, modcontractual):
        parent = super(GiscedataFacturacioFacturador, self).get_tarifa_class
        if modcontractual.mode_facturacio == 'index' or modcontractual.mode_facturacio_generacio == 'index':
            return TARIFFS_FACT[modcontractual.tarifa.name]
        else:
            return parent(modcontractual)

    def versions_de_preus(self, cursor, uid, polissa_id, data_inici,
                          data_final, context=None):
        res = super(GiscedataFacturacioFacturador, self).versions_de_preus(
            cursor, uid, polissa_id, data_inici, data_final, context
        )

        pricelist_obj = self.pool.get('product.pricelist')
        polissa_obj = self.pool.get('giscedata.polissa')
        imd_obj = self.pool.get('ir.model.data')

        # Afegim els productes nous
        gdos_som = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_gdos_som'
        )[1]
        factor_dsv = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada_som', 'product_factor_dsv_som'
        )[1]
        # Fem un browse amb la data final per obtenir quin mode de facturació té
        polissa = polissa_obj.browse(cursor, uid, polissa_id, context={
            'date': data_final
        })

        ctx = context.copy()

        if polissa.mode_facturacio == 'index' or polissa.mode_facturacio_generacio == 'index':
            if context.get('llista_preu', False):
                llista_preu_id = context['llista_preu']
            else:
                llista_preu_id = polissa.llista_preu.id

            for date_version in res:
                ctx['date'] = date_version
                res[date_version]['gdos'] = pricelist_obj.price_get(
                    cursor, uid, [llista_preu_id], gdos_som, 1, context=ctx
                )[llista_preu_id]
                res[date_version]['factor_dsv'] = pricelist_obj.price_get(
                    cursor, uid, [llista_preu_id], factor_dsv, 1, context=ctx
                )[llista_preu_id]

                if pricelist_obj.browse(cursor, uid, llista_preu_id).indexed_formula == u'Indexada Península':
                    # Fem un browse amb la data final per obtenir quina tarifa té
                    polissa = polissa_obj.browse(cursor, uid, polissa_id, context=ctx)
                    res[date_version]['h'] = polissa.coeficient_h * 0.001  # H is expressed in €/MWh in contract

        return res


GiscedataFacturacioFacturador()
