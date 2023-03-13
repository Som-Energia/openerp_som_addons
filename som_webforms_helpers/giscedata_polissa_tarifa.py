# -*- coding: utf-8 -*-
from osv import osv
from tools import config
from datetime import datetime

class GiscedataPolissaTarifa(osv.osv):
    _name = 'giscedata.polissa.tarifa'
    _inherit = 'giscedata.polissa.tarifa'

    _cosfi = [
        ('0', '0 - 0.80'),
        ('85', '0.80 - 0.95')
    ]

    _desc_tipus = {
        'tp': 'potencia',
        'te': 'energia',
        'tr': 'reactiva',
        'ep': 'exces_potencia',
        'epm': 'exces_potencia_per_maximetre',
        'ex': 'excedent_autoconsum',
        'ac': 'energia_autoconsumida',
        'rc': 'reactiva_capacitiva',
        'ec': 'energia_carrecs',
        'pc': 'potencia_carrecs',
        'gkwh': 'generation_kWh'
    }
    def get_products(self, cursor, uid, tarifa, context=None):
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        facturador_obj = self.pool.get('giscedata.facturacio.facturador')
        periode_productes = {}
        for periode in tarifa.periodes:
            products = []
            periode_productes[periode.product_id.id]= {'name': periode.name}
            products.append((periode.tipus, periode.product_id.id))
            if periode.tipus == 'te' and periode.product_gkwh_id:
                product_gkwh_id = fact_obj.get_gkwh_period(
                        cursor, uid, periode.product_id.id, context=context
                    )
                if product_gkwh_id:
                    products.append(('gkwh', product_gkwh_id, periode.product_id.id))
            if periode.product_reactiva_id:
                products.append(('tr', False, periode.product_reactiva_id.id))
            if periode.product_exces_pot_id:
                products.append(('ep', periode.product_exces_pot_id.id))
            if periode.product_exces_pot_max_id:
                products.append(('epm', periode.product_exces_pot_max_id.id))
            if periode.product_excedent_ac_id:
                product_id = facturador_obj.get_productes_autoconsum(cursor, uid, tipus='autoconsum', tarifa_id=tarifa.id,  context=context)[periode.name]
                products.append(('ex', product_id))
            if periode.product_autoconsum_ac_id:
                product_id = facturador_obj.get_productes_autoconsum(cursor, uid, tipus='excedent', tarifa_id=tarifa.id,  context=context)[periode.name]
                products.append(('ac', product_id))
            if periode.product_reactiva_capacitiva_id:
                products.append(('rc', periode.product_reactiva_capacitiva_id.id))
            if periode.product_energia_carrecs_id:
                products.append(('ec', periode.product_energia_carrecs_id.id))
            if periode.product_potencia_carrecs_id:
                products.append(('pc', periode.product_potencia_carrecs_id.id))

            periode_productes[periode.product_id.id]['products'] = products

        return periode_productes

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

    def _get_som_price_version_list(self, cursor, uid, municipi_id, pricelist_list, date_from, date_to, context):
        municipi_obj = self.pool.get('res.municipi')
        pricelist_municipi = municipi_obj.filter_compatible_pricelists(
            cursor, uid, municipi_id=municipi_id,
            pricelist_list=pricelist_list, context=context)

        price_version_list = []
        for item in pricelist_municipi:
            versions = item.version_id
            for version in versions:
                date_start = version.date_start
                date_end = version.date_end
                if version.active and (not date_end or date_from <= date_end) and \
                    (not date_start or date_to >= date_start):
                    price_version_list.append(version)

        return price_version_list

    def _get_general_price_version_list(self, cursor, uid, pricelist_list, date_from, date_to):
        pricelist_general = [item for item in pricelist_list if item.name == 'TARIFAS ELECTRICIDAD']

        general_price_version_list = []
        if pricelist_general:
            versions = pricelist_general[0].version_id
            for version in versions:
                date_start = version.date_start
                date_end = version.date_end
                if version.active and (not date_end or date_from <= date_end) and \
                    (not date_start or date_to >= date_start):
                    general_price_version_list.append(version)

        return general_price_version_list

    def _get_fiscal_position(self, cursor, uid, fiscal_position_id, date_from, date_to, max_power):
        conf_obj = self.pool.get('res.config')
        prop_obj = self.pool.get('ir.property')
        imd_obj = self.pool.get('ir.model.data')
        fp_obj = self.pool.get('account.fiscal.position')

        fiscal_position = None
        if not fiscal_position_id:
            start_date_iva_reduit = conf_obj.get(
              cursor, uid, 'iva_reduit_get_tariff_prices_start_date', '2021-06-01'
            )
            end_date_iva_reduit = conf_obj.get(
              cursor, uid, 'iva_reduit_get_tariff_prices_end_date', '2099-12-31'
            )
            if (date_from <= end_date_iva_reduit and date_to >= start_date_iva_reduit) and max_power <= 10000:
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

        return fiscal_position

    def get_reactiva_cosfi_prices(self, cursor, uid, pricelist, context=None):
        fact_obj = self.pool.get('giscedata.facturacio.facturador')

        price_cosfi = []

        for cosfi in self._cosfi:
            price = fact_obj.calc_cosfi_price(cursor, uid, cosfi[0], pricelist.id, context)
            price_cosfi.append({'cosfi': cosfi, 'price': price})

        return price_cosfi

    def get_reactiva_price(self, cursor, uid, general_price_version_list, price_version, context):
        reactiva_prices = []
        general_price_version_list_in_range = [
            item for item in general_price_version_list
            if (not item.date_end or not price_version.date_start or price_version.date_start <= item.date_end) and \
            (not item.date_start or not price_version.date_end or price_version.date_end >= item.date_start)]

        for general_price_version in general_price_version_list_in_range:

            cosfi_items =  self.get_reactiva_cosfi_prices(
                cursor, uid, general_price_version.pricelist_id, context=context
            )
            for cosfi_item in cosfi_items:
                cosfi_desc = general_price_version.name
                cosfi_value = cosfi_item['cosfi'][1]
                cosfi_price = cosfi_item['price']

                reactiva_price = (cosfi_price, 'kVArh', cosfi_desc, cosfi_value)
                reactiva_prices.append(reactiva_price)

        return reactiva_prices

    def get_tariff_prices(self, cursor, uid, tariff_id, municipi_id, max_power,
                          fiscal_position_id=None, with_taxes=False,
                          date_from=False, date_to=False, context=None):
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
        uom_obj = self.pool.get('product.uom')
        prod_obj = self.pool.get('product.product')

        # get default pricelist for this tariff
        tariff = tariff_obj.browse(cursor, uid, tariff_id)
        pricelist_list = tariff.llistes_preus_comptatibles

        if not date_from and not date_to:
            date_from = date_to = datetime.today().strftime('%Y-%m-%d')

        som_price_version_list = self._get_som_price_version_list(
            cursor, uid, municipi_id, pricelist_list, date_from, date_to, context)

        general_price_version_list = self._get_general_price_version_list(
            cursor, uid, pricelist_list, date_from, date_to)

        fiscal_position = self._get_fiscal_position(
            cursor, uid, fiscal_position_id, max_power, date_from, date_to)

        if not som_price_version_list:
            return [dict(
                error= 'Tariff pricelist not found'
            )]

        periodes_products = self.get_products(cursor, uid, tariff, context=None)

        price_by_date_range = []
        for price_version in som_price_version_list:

            context = {
                'date': price_version.date_start,
            }

            preus = {}  # dictionary to be returned

            product_price_list = price_version.pricelist_id

            reactive_prices_without_taxes = self.get_reactiva_price(
                cursor, uid, general_price_version_list, price_version, context
            )

            items_ids = [item for item in price_version.items_id if item.base == -3]

            for item in items_ids:

                product_id = item.product_id.id

                if product_id not in periodes_products.keys():
                    continue

                name = periodes_products[product_id]['name']

                tipus_products = periodes_products[product_id]['products']

                for tipus_product in tipus_products:

                    tipus = tipus_product[0]
                    product_tipus_id = tipus_product[1]

                    if self._desc_tipus[tipus] not in preus:
                        preus[self._desc_tipus[tipus]] = {}

                    if tipus != 'tr':
                        # taxes for gkwh are calculated later and taxes for autoconsum
                        # are not calculated
                        apply_taxes = with_taxes and tipus not in ['gkwh']

                        value, discount, uom_id = product_price_list.get_atr_price(
                            tipus=tipus, product_id=product_tipus_id,
                            fiscal_position=fiscal_position, context=context,
                            with_taxes=apply_taxes, direccio_pagament=None,
                            titular=None
                        )

                    if tipus == 'gkwh' and with_taxes:
                        tax_product = tipus_product[2]

                        value = prod_obj.add_taxes(
                            cursor, uid, tax_product, value,
                            fiscal_position, direccio_pagament=None,
                            titular=None
                        )

                    reactive_prices = []
                    if tipus == 'tr':
                        if with_taxes:
                            tax_product = tipus_product[2]

                            for reactive_price in reactive_prices_without_taxes:
                                reactive_price_list = list(reactive_price)
                                reactive_price_list[0] = prod_obj.add_taxes(
                                    cursor, uid, tax_product, reactive_price_list[0],
                                    fiscal_position, direccio_pagament=None,
                                    titular=None
                                )
                                reactive_prices.append(tuple(reactive_price_list))
                        else:
                            reactive_prices = reactive_prices_without_taxes

                        for cosfi_price, unit, cosfi_desc, cosfi_value in reactive_prices:
                            if not cosfi_desc in preus[self._desc_tipus['tr']]:
                                preus[self._desc_tipus['tr']][cosfi_desc] = {}

                            preus[self._desc_tipus['tr']][cosfi_desc][cosfi_value] = {
                                'value': round(cosfi_price, config.get('price_accuracy', 6)),
                                'unit': '€/{}'.format(unit)
                            }
                    else:
                        # units of measure
                        uom = uom_obj.browse(cursor, uid, uom_id)
                        preus[self._desc_tipus[tipus]][name] = {
                            'value': round(value, config.get('price_accuracy', 6)),
                            'unit': '€/{}'.format(uom.name if uom.name != 'PCE' else 'kWh')
                        }

            value, uom = self.get_bo_social_price(
                cursor, uid, product_price_list, fiscal_position=fiscal_position, with_taxes=with_taxes, context=context
            )
            preus['bo_social'] = {
                'value': round(value, config.get('price_accuracy', 6)),
                'unit': '€/{}'.format(uom.name)
            }

            value, uom = self.get_comptador_price(
                cursor, uid, product_price_list, fiscal_position=fiscal_position, with_taxes=with_taxes, context=context
            )
            preus['comptador'] = {
                'value': round(value, config.get('price_accuracy', 6)),
                'unit':  '€{}'.format(('/' + uom.name.split('/')[1]) if '/' in uom.name else '')
            }

            preus['version_name'] = price_version.name
            preus['start_date'] = price_version.date_start
            preus['end_date'] = price_version.date_end

            price_by_date_range.append(preus)

        return price_by_date_range


GiscedataPolissaTarifa()
