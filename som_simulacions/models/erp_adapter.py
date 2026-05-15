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
        return None

    def _get_company_default_value(self, cr, uid, concept_name, when_date,
                                   context=None):
        return None

    def _get_value_with_fallback(self, cr, uid, concept_name, when_date,
                                 tariff_code=None, context=None):
        value = self._get_tariff_specific_value(
            cr, uid, concept_name, when_date, tariff_code=tariff_code,
            context=context
        )
        if value:
            return {
                'value': value.get('value'),
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
