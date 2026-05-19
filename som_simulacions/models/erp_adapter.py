# -*- coding: utf-8 -*-
from osv import osv


class SomSimulacioErpAdapter(osv.osv):
    _name = 'som.simulacio.erp.adapter'
    _description = 'Indexed estimate fixed-concept adapter'

    def _raise_missing_value(self, concept_name):
        raise osv.except_osv('Missing configuration',
                             'No value found for concept: %s' % concept_name)

    def _get_tariff_specific_value(self, cr, uid, concept_name, when_date,
                                   tariff_code=None, context=None):
        if concept_name == 'power_price':
            return self._get_tariff_power_price(
                cr, uid, when_date, tariff_code=tariff_code, context=context
            )
        if concept_name == 'social_bonus':
            return self._get_tariff_product_value(
                cr, uid, when_date, tariff_code, 'bosocial_BS01', context=context
            )
        if concept_name == 'meter_charge':
            value = self._get_tariff_product_value(
                cr, uid, when_date, tariff_code, 'alq_conta_tele', context=context
            )
            if value:
                return value
            return self._get_tariff_product_value(
                cr, uid, when_date, tariff_code, 'ALQ01',
                use_default_code=True, context=context
            )
        return None

    def _get_company_default_value(self, cr, uid, concept_name, when_date,
                                   context=None):
        if concept_name == 'social_bonus':
            return self._get_global_product_value(
                cr, uid, when_date,
                module_name='giscedata_repercusio_bo_social',
                xml_or_code='bosocial_BS01',
                context=context,
            )

        if concept_name == 'meter_charge':
            value = self._get_global_product_value(
                cr, uid, when_date,
                module_name='giscedata_lectures',
                xml_or_code='alq_conta_tele',
                context=context,
            )
            if value:
                return value
            return self._get_global_product_value(
                cr, uid, when_date,
                module_name=None,
                xml_or_code='ALQ01',
                use_default_code=True,
                context=context,
            )
        return None

    def _get_concept_product_price(self, cr, uid, product_id, when_date,
                                   context=None):
        ctx = dict(context or {})
        if when_date:
            ctx['date'] = when_date

        pricelist_id = ctx.get('pricelist_id') or ctx.get('force_pricelist')
        if pricelist_id:
            pricelist_obj = self.pool.get('product.pricelist')
            values = pricelist_obj.price_get(
                cr, uid, [pricelist_id], product_id, 1, context=ctx
            )
            return values.get(pricelist_id) or 0.0

        product_obj = self.pool.get('product.product')
        product = product_obj.read(cr, uid, product_id, ['list_price'], context=ctx)
        return product.get('list_price') or 0.0

    def _find_tariff(self, cr, uid, tariff_code, context=None):
        if not tariff_code:
            return False
        tariff_obj = self.pool.get('giscedata.polissa.tarifa')
        tariff_ids = tariff_obj.search(
            cr, uid, [('name', '=', tariff_code)], limit=1, context=context
        )
        return tariff_ids and tariff_ids[0] or False

    def _get_tariff_product_value(self, cr, uid, when_date, tariff_code,
                                  xml_or_code, use_default_code=False,
                                  context=None):
        tariff_id = self._find_tariff(cr, uid, tariff_code, context=context)
        if not tariff_id:
            return None

        product_id = False
        if use_default_code:
            product_obj = self.pool.get('product.product')
            product_ids = product_obj.search(
                cr, uid, [('default_code', '=', xml_or_code)], limit=1, context=context
            )
            product_id = product_ids and product_ids[0] or False
        else:
            imd_obj = self.pool.get('ir.model.data')
            module_name = 'giscedata_repercusio_bo_social'
            if xml_or_code == 'alq_conta_tele':
                module_name = 'giscedata_lectures'
            try:
                product_id = imd_obj.get_object_reference(
                    cr, uid, module_name, xml_or_code
                )[1]
            except Exception:
                product_id = False

        if not product_id:
            return None

        value = self._get_concept_product_price(
            cr, uid, product_id, when_date, context=context
        )
        return {
            'value': value,
            'record_id': product_id,
        }

    def _get_global_product_value(self, cr, uid, when_date, module_name,
                                  xml_or_code, use_default_code=False,
                                  context=None):
        product_id = False
        if use_default_code:
            product_obj = self.pool.get('product.product')
            product_ids = product_obj.search(
                cr, uid, [('default_code', '=', xml_or_code)], limit=1, context=context
            )
            product_id = product_ids and product_ids[0] or False
        else:
            imd_obj = self.pool.get('ir.model.data')
            try:
                product_id = imd_obj.get_object_reference(
                    cr, uid, module_name, xml_or_code
                )[1]
            except Exception:
                product_id = False

        if not product_id:
            return None

        value = self._get_concept_product_price(
            cr, uid, product_id, when_date, context=context
        )
        return {
            'value': value,
            'record_id': product_id,
        }

    def _get_tariff_power_price(self, cr, uid, when_date, tariff_code=None,
                                context=None):
        tariff_id = self._find_tariff(cr, uid, tariff_code, context=context)
        if not tariff_id:
            return None

        tariff_obj = self.pool.get('giscedata.polissa.tarifa')
        period_products = tariff_obj.get_periodes_producte(
            cr, uid, tariff_id, 'tp', context=context
        )
        if not period_products:
            return None

        p1_id = period_products.get('P1')
        p2_id = period_products.get('P2')
        if not p1_id and not p2_id:
            return None

        p1_value = p1_id and self._get_concept_product_price(
            cr, uid, p1_id, when_date, context=context
        ) or 0.0
        p2_value = p2_id and self._get_concept_product_price(
            cr, uid, p2_id, when_date, context=context
        ) or 0.0

        return {
            'value': 0.0,
            'components': {
                'p1': p1_value,
                'p2': p2_value,
            },
            'record_id': tariff_id,
        }

    def _get_value_with_fallback(self, cr, uid, concept_name, when_date,
                                 tariff_code=None, context=None):
        value = self._get_tariff_specific_value(
            cr, uid, concept_name, when_date, tariff_code=tariff_code,
            context=context
        )
        if value:
            return {
                'value': value.get('value'),
                'components': value.get('components'),
                'source': 'tariff',
                'record_id': value.get('record_id'),
                'fallback_used': False,
            }

        value = self._get_company_default_value(
            cr, uid, concept_name, when_date, context=context
        )
        if value:
            return {
                'value': value.get('value'),
                'components': value.get('components'),
                'source': 'default',
                'record_id': value.get('record_id'),
                'fallback_used': True,
            }

        self._raise_missing_value(concept_name)

    def get_power_price(self, cr, uid, when_date, tariff_code=None, context=None):
        return self._get_value_with_fallback(
            cr, uid, 'power_price', when_date,
            tariff_code=tariff_code, context=context
        )

    def get_social_bonus(self, cr, uid, when_date, tariff_code=None, context=None):
        return self._get_value_with_fallback(
            cr, uid, 'social_bonus', when_date,
            tariff_code=tariff_code, context=context
        )

    def get_meter_charge(self, cr, uid, when_date, tariff_code=None, context=None):
        return self._get_value_with_fallback(
            cr, uid, 'meter_charge', when_date,
            tariff_code=tariff_code, context=context
        )


SomSimulacioErpAdapter()
