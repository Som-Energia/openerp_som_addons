# -*- coding: utf-8 -*-
from osv import osv
from .tarifes import TARIFFS_FACT
from libfacturacioatr.pool.tarifes import *


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
        reganecu_obj = self.pool.get('giscedata.reganecu')

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
                res[date_version]['bs3qh'] = reganecu_obj.get_reganecu_components_between_dates(
                    cursor, uid, data_inici, data_final, 'BS3', context=ctx
                )
                res[date_version]['rad3qh'] = reganecu_obj.get_reganecu_components_between_dates(
                    cursor, uid, data_inici, data_final, 'RAD3', context=ctx
                )

                if pricelist_obj.browse(cursor, uid, llista_preu_id).indexed_formula == u'Indexada Península':
                    # Fem un browse amb la data final per obtenir quina tarifa té
                    polissa = polissa_obj.browse(cursor, uid, polissa_id, context=ctx)
                    res[date_version]['h'] = polissa.coeficient_h * 0.001  # H is expressed in €/MWh in contract

        return res

    # Serveis d'ajust a preu fix
    def avoid_creating_zero_lines(self, cursor, uid, factura_id, servei_vals, context=None):
        return 'data_inici' in servei_vals and servei_vals.get('data_inici') < '2026-05-01'

    def get_consum_curve_components_for_servei(self, cursor, uid, fact_id, data_inici, data_final,
                                               single_period_profiling, context=None):
        if context is None:
            context = {}
        tmp_curves = super(GiscedataFacturacioFacturador, self).get_consum_curve_components_for_servei(
            cursor, uid, fact_id, data_inici, data_final, single_period_profiling, context=context
        )
        res = []
        for curve in tmp_curves:
            if curve.start_date.strftime('%Y-%m-%d') < '2026-05-01':
                curve = curve * 0
            res.append(curve)
        return res

    def get_audit_keys_calc_preu_servei_ajust(self, cursor, uid):
        return {'corba_sa': 'curve'}

    def get_audit_keys_phf_calc_servei_ajust(self, cursor, uid):
        return {'prdemcad_sa': 'prdemcad', 'perdues_sa': 'perdues'}

    def phf_calc_servei_ajust(self, cursor, uid, factura, tariff, esios_token, start_date, end_date,
                              context=None):
        if context is None:
            context = {}

        if start_date.strftime("%Y-%m-%d") >= '2026-05-01':
            postfix = '%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))
            fname = tariff.perdclass.name
            perdues = tariff.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)
            prdemcad = Prdemcad('C2_prdemcad_%(postfix)s' % locals(), esios_token)  # prdemcad [€/MWh]
        else:
            perdues = Component(start_date)
            prdemcad = Component(start_date)

        A = (prdemcad * 0.001)
        B = (1 + (perdues * 0.01))
        C = A * B

        audit_keys = self.get_audit_keys_phf_calc_servei_ajust(cursor, uid)
        for key in audit_keys.keys():
            if key not in tariff.audit_data.keys():
                tariff.audit_data[key] = []
            if key not in tariff.audit_components.keys():
                tariff.audit_components[key] = None
            var_name = audit_keys[key]
            com = locals()[var_name]
            tariff.audit_components[key] = com
            tariff.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return C


GiscedataFacturacioFacturador()


class GiscedataNextDaysEnergyPrice(osv.osv):
    _inherit = 'giscedata.next.days.energy.price'

    def get_tarifa_class(self, cursor, uid, tarifa_name, context=None):
        return TARIFFS_FACT[tarifa_name]

GiscedataNextDaysEnergyPrice()
