# -*- coding: utf-8 -*-
from osv import osv
from tools import config
from datetime import datetime, timedelta
from enerdata.contracts import get_tariff_by_code
from enerdata.contracts.normalized_power import NormalizedPower

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

    def _get_default_fiscal_position_id(self, cursor, uid, date_from, date_to):
        prop_obj = self.pool.get('ir.property')
        fp_obj = self.pool.get('account.fiscal.position')

        fiscal_position_data = []

        prop_id = prop_obj.search(cursor,uid,[('name','=','property_account_position'),('res_id','=',False)])
        if isinstance(prop_id,list):
            prop_id = prop_id[0]
        prop=prop_obj.browse(cursor, uid, prop_id)
        if prop.value:
            fiscal_position_id = int(prop.value.split(',')[1])
            fiscal_position = fp_obj.browse(cursor, uid, fiscal_position_id)
            fiscal_position_data.append((date_from, date_to, fiscal_position))

        return fiscal_position_data

    def _get_fiscal_position_reduced(self, cursor, uid, max_power, date_from, date_to):
        conf_obj = self.pool.get('res.config')
        imd_obj = self.pool.get('ir.model.data')
        fp_obj = self.pool.get('account.fiscal.position')

        fiscal_position_data = []

        start_date_iva_reduit = conf_obj.get(
            cursor, uid, 'iva_reduit_get_tariff_prices_start_date', '2021-06-01'
        )
        end_date_iva_reduit = conf_obj.get(
            cursor, uid, 'iva_reduit_get_tariff_prices_end_date', '2099-12-31'
        )
        if (date_from <= end_date_iva_reduit and date_to >= start_date_iva_reduit) and max_power <= 10000:
            fiscal_position_id = imd_obj.get_object_reference(cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
            fiscal_position = fp_obj.browse(cursor, uid, fiscal_position_id)
            fiscal_position_data.append((start_date_iva_reduit, end_date_iva_reduit, fiscal_position))

        return fiscal_position_data

    def _get_fiscal_position_igic(self, cursor, uid, date_from, date_to, home):
        conf_obj = self.pool.get('res.config')
        fp_obj = self.pool.get('account.fiscal.position')

        fiscal_position_data = []

        if not date_from and not date_to:
            date_from = date_to = datetime.today().strftime('%Y-%m-%d')

        taxes_ids_by_period = conf_obj.get(
            cursor, uid, 'fiscal_position_igic', []
        )

        for start_date_igic, end_date_igic, home_igic_tax_id, industrial_igic_tax_id in eval(taxes_ids_by_period):
            if (end_date_igic >= date_from and start_date_igic <= date_to):
                fiscal_position_id = home_igic_tax_id if home else industrial_igic_tax_id
                fiscal_position = fp_obj.browse(cursor, uid, fiscal_position_id)
                fiscal_position_data.append((start_date_igic, end_date_igic, fiscal_position))

        return fiscal_position_data

    def _get_fiscal_position(self, cursor, uid, fiscal_position_id, date_from, date_to, max_power, municipi_id, home):
        municipi_obj = self.pool.get('res.municipi')
        fp_obj = self.pool.get('account.fiscal.position')

        date_to = datetime.today().strftime('%Y-%m-%d') if not date_to else date_to

        fiscal_position_data = []

        fiscal_position_reduced_data = self._get_fiscal_position_reduced(cursor, uid, max_power, date_from, date_to)
        fiscal_position_data.extend(fiscal_position_reduced_data)

        if not fiscal_position_id:
            municipi = municipi_obj.browse(cursor, uid, municipi_id)
            if municipi.subsistema_id.code != 'PE':
                # IGIC
                fiscal_position_igic_data = self._get_fiscal_position_igic(cursor, uid, date_from, date_to, home)
                fiscal_position_data.extend(fiscal_position_igic_data)
            else:
                fiscal_position_default_data = self._get_default_fiscal_position_id(cursor, uid, date_from, date_to)
                fiscal_position_data.extend(fiscal_position_default_data)
        else:
            fiscal_position = fp_obj.browse(cursor, uid, fiscal_position_id)
            fiscal_position_data.append((date_from, date_to, fiscal_position))

        return fiscal_position_data

    def _get_reactiva_cosfi_prices(self, cursor, uid, pricelist, context=None):
        fact_obj = self.pool.get('giscedata.facturacio.facturador')

        price_cosfi = []

        for cosfi in self._cosfi:
            price = fact_obj.calc_cosfi_price(cursor, uid, cosfi[0], pricelist.id, context)
            price_cosfi.append({'cosfi': cosfi, 'price': price})

        return price_cosfi

    def _get_reactiva_price(self, cursor, uid, general_price_version_list, price_version, context):
        reactiva_prices = []
        general_price_version_list_in_range = [
            item for item in general_price_version_list
            if (not item.date_end or not price_version.date_start or price_version.date_start <= item.date_end) and \
            (not item.date_start or not price_version.date_end or price_version.date_end >= item.date_start)]

        for general_price_version in general_price_version_list_in_range:

            cosfi_items =  self._get_reactiva_cosfi_prices(
                cursor, uid, general_price_version.pricelist_id, context=context
            )
            for cosfi_item in cosfi_items:
                cosfi_desc = general_price_version.name
                cosfi_value = cosfi_item['cosfi'][1]
                cosfi_price = cosfi_item['price']

                reactiva_price = (cosfi_price, 'kVArh', cosfi_desc, cosfi_value)
                reactiva_prices.append(reactiva_price)

        return reactiva_prices

    def _get_max_power_by_tariff(self, tariff_name):
        tariff_max_power = None
        tarifa_enerdata = get_tariff_by_code(tariff_name)
        if tarifa_enerdata:
            tarifa_enerdata = tarifa_enerdata()
            tariff_max_power = tarifa_enerdata.get_max_power()
            tariff_max_power *= 1000
        return tariff_max_power

    def _combine_pricelist_fiscal_position(self, pricelists, fiscal_positions):
        pricelist_data = []

        if fiscal_positions:
            ordered_fiscal_position = sorted(fiscal_positions, key=lambda element: (element[0], element[1]))
            pricelists.sort(key = lambda element: (element.date_start, element.date_end))

            for pl in pricelists:
                for fp_date_start, fp_date_end, fp in ordered_fiscal_position:
                    if fp_date_end >= pl.date_start or pl.date_end or fp_date_start <= pl.date_end:
                        pricelist_data.append(tuple((pl, fp)))
        else:
            for pl in pricelists:
                pricelist_data.append(tuple((pl, None)))

        return pricelist_data

    def get_tariff_prices(self, cursor, uid, tariff_id, municipi_id, max_power=None,
                          fiscal_position_id=None, with_taxes=False, home=True,
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
        context['pricelist_base_price'] = 0.0

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

        if not som_price_version_list:
            return [dict(
                error= 'Tariff pricelist not found'
            )]

        general_price_version_list = self._get_general_price_version_list(
            cursor, uid, pricelist_list, date_from, date_to)

        if not max_power:
            max_power = self._get_max_power_by_tariff(tariff.name)

        fiscal_position_data = self._get_fiscal_position(cursor, uid, fiscal_position_id,
            date_from, date_to, max_power, municipi_id, home)

        som_price_list_version_data = self._combine_pricelist_fiscal_position(som_price_version_list, fiscal_position_data)

        periodes_products = self.get_products(cursor, uid, tariff, context=None)

        price_by_date_range = {'tariff_id': tariff_id, 'prices':[]}
        for price_version, fiscal_position in som_price_list_version_data:

            context['date'] = price_version.date_start

            preus = {}  # dictionary to be returned

            product_price_list = price_version.pricelist_id

            reactive_prices_without_taxes = self._get_reactiva_price(
                cursor, uid, general_price_version_list, price_version, context
            )

            for item in price_version.items_id:

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
                preus['fiscal_position'] = fiscal_position.name if fiscal_position else False

            price_by_date_range['prices'].append(preus)

        return price_by_date_range

    def _validate_modcons(self, modcon_data):
        consistent_data = True
        ant = modcon_data[0]

        for modcon in modcon_data[1:]:
            next_day = datetime.strptime(ant[4], '%Y-%m-%d') + timedelta(days=1)
            initial_day = datetime.strptime(modcon[3], '%Y-%m-%d')
            if initial_day == next_day:
                ant = modcon
            else:
                consistent_data = False
                break
        return consistent_data

    def _get_dades_modcontractuals(self, modcon_data):

        ordered_modcon_data = sorted(modcon_data, key=lambda element: (element[3], element[4]))

        consistent_data = self._validate_modcons(ordered_modcon_data)

        reduced_modcon_data = []
        if consistent_data:
            ant = list(ordered_modcon_data[0])
            last = list(ordered_modcon_data[-1])
            for c in ordered_modcon_data:
                if len(set(list(c)[0:3] + list(ant)[0:3])) == 3:
                    ant[4] = c[4]
                    continue
                reduced_modcon_data.append(tuple(ant))
                ant = list(c)

            if len(set(list(last)[0:3] + list(ant)[0:3])) == 3:
                ant[4] = last[4]
            reduced_modcon_data.append(tuple(ant))

        return reduced_modcon_data

    def get_tariff_prices_by_contract_id(self, cursor, uid, contract_id, with_taxes=False, context=None):
        pol_obj = self.pool.get('giscedata.polissa')

        polissa = pol_obj.browse(cursor, uid, contract_id)
        municipi_id = polissa.titular.address[0].id_municipi.id
        home = True if polissa.tipus_vivenda == 'habiual' else False
        modcontractuals = polissa.modcontractuals_ids

        modcon_data = []
        for mod in modcontractuals:
            fiscal_position = False
            if mod.fiscal_position_id:
                fiscal_position = mod.fiscal_position_id
            modcon_data.append((mod.tarifa.id, fiscal_position, mod.potencia, mod.data_inici, mod.data_final))

        pricelist_data = self._get_dades_modcontractuals(modcon_data)

        prices_by_contract = []

        for tariff_id, fiscal_position_id, max_power, date_from, date_to in pricelist_data:

            max_power = max_power * 1000 if max_power else 10000

            price_by_date_range = self.get_tariff_prices(cursor, uid, int(tariff_id), municipi_id, max_power,
                            int(fiscal_position_id), with_taxes, home,
                            date_from, date_to, context)
            prices_by_contract.append(price_by_date_range)

        return prices_by_contract

GiscedataPolissaTarifa()
