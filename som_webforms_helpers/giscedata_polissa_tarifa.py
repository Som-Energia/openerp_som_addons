# -*- coding: utf-8 -*-
from osv import osv
from tools import config
from datetime import datetime

class GiscedataPolissaTarifa(osv.osv):
    _name = 'giscedata.polissa.tarifa'
    _inherit = 'giscedata.polissa.tarifa'

    def __get_all_periods(self, cursor, uid, tarifa, context):
        facturador_obj = self.pool.get('giscedata.facturacio.facturador')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        period_obj = self.pool.get('giscedata.polissa.tarifa.periodes')
        periods = []
        ctx = {'sense_agrupar': True, 'date': False}
        periodes_tarifa = tarifa.get_periodes(context=ctx).values()
        periodes_tarifa.extend(tarifa.get_periodes('tp', context=ctx).values())
        # tariff.periodes only contain power (tp) and energy (te) terms
        for periode in period_obj.browse(cursor, uid, periodes_tarifa):
            # build a dictionary list with the information needed to
            # calculate prices
            periods.append({
                'name': periode.name,  # P1, P2...
                'tipus': periode.tipus,  # te or tp
                'product_id': periode.product_id.id
            })

            # gkwh has the same amount of periods as the energy term
            if periode.tipus == 'te':
                periods.append({
                    'name': periode.name,  # P1, P2...
                    'tipus': 'gkwh',
                    'product_id': fact_obj.get_gkwh_period(
                        cursor, uid, periode.product_id.id, context=context
                    ),
                    'taxes_product_id': periode.product_id.id
                })

        # append autoconsum (ac) term
        periodes_ac = facturador_obj.get_productes_autoconsum(
            cursor, uid, tipus="excedent", context=context
        )
        periods.append({
            'name': 'P1',
            'tipus': 'ac',
            'product_id': periodes_ac['P1']
        })

        return periods

    def get_bo_social_price(self, cursor, uid, pricelist,
                          fiscal_position=None, with_taxes=False,
                          context=None):
        imd_obj = self.pool.get('ir.model.data')
        prod_obj = self.pool.get('product.product')

        bs_id = imd_obj.get_object_reference(cursor, uid, 'som_polissa_soci', 'bosocial_BS01')[1]
        prod = prod_obj.browse(cursor, uid, bs_id)

        price = pricelist.price_get(bs_id, 1, 1, context)[pricelist.id]
        if with_taxes:
            price = prod.add_taxes(price, fiscal_position, direccio_pagament=None,
                    titular=None)

        return price, prod.uom_id

    def get_comptador_price(self, cursor, uid, pricelist,
                          fiscal_position=None, with_taxes=False,
                          context=None):
        imd_obj = self.pool.get('ir.model.data')
        prod_obj = self.pool.get('product.product')

        comptador_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_lectures', 'alq_conta_tele')[1]

        price = pricelist.price_get(comptador_id, 1, 1, context)[pricelist.id]

        default_comptador_id = prod_obj.search(cursor, uid,
                                [('default_code', '=', 'ALQ01')])

        prod = prod_obj.browse(cursor, uid, comptador_id)
        if with_taxes:
            if default_comptador_id:
                comptador_id = default_comptador_id[0]

            price = prod_obj.add_taxes(cursor, uid, comptador_id, price, fiscal_position, direccio_pagament=None,
                    titular=None)

        return price, prod.uom_id

    def get_tariff_prices(self, cursor, uid, tariff_id, municipi_id, max_power,
                          fiscal_position_id=None, with_taxes=False,
                          date=False, context=None):
        """
            Returns a dictionary with the prices of the given tariff.
            Example of return value:
            {
                'bo_social': {
                    {'value': 0.123, 'uom': '€/dia'}
                },
                'comptador': {
                    {'value': 0.123, 'uom': '€/mes'}
                },
                'te': {
                    'P1': {'value': 0.123, 'uom': '€/KW dia'}
                },
                'tp': {
                    'P1': {'value': 0.123, 'uom': '€/KW dia'},
                    'P2': {'value': 0.234, 'uom': '€/KW dia'}
                },
                ...
            }

        """
        if context is None:
            context = {}

        if isinstance(tariff_id, (list, tuple)):
            tariff_id = tariff_id[0]

        tariff_obj = self.pool.get('giscedata.polissa.tarifa')
        municipi_obj = self.pool.get('res.municipi')
        fp_obj = self.pool.get('account.fiscal.position')
        uom_obj = self.pool.get('product.uom')
        prod_obj = self.pool.get('product.product')
        prop_obj = self.pool.get('ir.property')
        conf_obj = self.pool.get('res.config')
        imd_obj = self.pool.get('ir.model.data')

        # get default pricelist for this tariff
        tariff = tariff_obj.browse(cursor, uid, tariff_id)
        pricelist_list = tariff.llistes_preus_comptatibles
        pricelist_municipi = municipi_obj.filter_compatible_pricelists(
            cursor, uid, municipi_id=municipi_id,
            pricelist_list=pricelist_list, context=context)

        if not date:
            pricelist = pricelist_municipi
            date = datetime.today().strftime('%Y-%m-%d')
        else:
            pricelist = []
            for item in pricelist_municipi:
                versions = item.version_id
                for version in versions:
                    date_start = version.date_start
                    date_end = version.date_end
                    if (not date_start or date_start <= date) and \
                        (not date_end or date_end >= date):
                        pricelist.append(item)

        fiscal_position = None
        if not fiscal_position_id:
            end_iva_reduit = conf_obj.get(
              cursor, uid, 'iva_reduit_get_tariff_prices_end_date', '2099-12-31'
            )
            if date <= end_iva_reduit and max_power <= 10000:
                fiscal_position_id = imd_obj.get_object_reference(cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
            else:
                prop_id = prop_obj.search(cursor,uid,[('name','=','property_account_position'),('res_id','=',False)])
                if isinstance(prop_id,list):
                    prop_id = prop_id[0]
                prop=prop_obj.browse(cursor, uid, prop_id)
                if prop.value:
                    fiscal_position_id = int(prop.value.split(',')[1])
        if fiscal_position_id:
            fiscal_position = fp_obj.browse(cursor, uid, fiscal_position_id)

        if not pricelist:
            raise osv.except_osv(
                'Warning !',
                'Tariff pricelist not found'
            )

        pricelist = pricelist[0]

        periods = self.__get_all_periods(cursor, uid, tariff, context)

        preus = {}  # dictionary to be returned
        for period in periods:

            if period['tipus'] not in preus:
                preus[period['tipus']] = {}

            product_id = period['product_id']

            # taxes for gkwh are calculated later and taxes for autoconsum
            # are not calculated
            apply_taxes = with_taxes and period['tipus'] not in ['gkwh']

            value, discount, uom_id = pricelist.get_atr_price(
                tipus=period['tipus'], product_id=product_id,
                fiscal_position=fiscal_position, context=context,
                with_taxes=apply_taxes, direccio_pagament=None,
                titular=None
            )

            # apply taxes of the energy term to gkwh price
            if with_taxes and period['tipus'] == 'gkwh':
                value = prod_obj.add_taxes(
                    cursor, uid, period['taxes_product_id'], value,
                    fiscal_position, direccio_pagament=None,
                    titular=None
                )

            # units of measure
            uom = uom_obj.browse(cursor, uid, uom_id)
            preus[period['tipus']][period['name']] = {
                'value': round(value, config.get('price_accuracy', 6)),
                'uom': '€/{}'.format(uom.name if uom.name != 'PCE' else 'kWh')
            }

        value, uom = self.get_bo_social_price(
            cursor, uid, pricelist, fiscal_position=fiscal_position, with_taxes=with_taxes, context=context
        )
        preus['bo_social'] = {
            'value': round(value, config.get('price_accuracy', 6)),
            'uom': '€/{}'.format(uom.name)
        }

        value, uom = self.get_comptador_price(
            cursor, uid, pricelist, fiscal_position=fiscal_position, with_taxes=with_taxes, context=context
        )
        preus['comptador'] = {
            'value': round(value, config.get('price_accuracy', 6)),
            'uom': '€/{}'.format(uom.name.split('/')[1])
        }

        return preus


GiscedataPolissaTarifa()
