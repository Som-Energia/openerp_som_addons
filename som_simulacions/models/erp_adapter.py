# -*- coding: utf-8 -*-
from osv import osv


class SomSimulacioErpAdapter(osv.osv):
    _name = 'som.simulacio.erp.adapter'
    _description = 'Indexed estimate fixed-concept adapter'

    def _raise_missing_value(self, concept_name):
        raise osv.except_osv('Missing configuration',
                             'No value found for concept: %s' % concept_name)

    def get_power_price(self, cr, uid, when_date, tariff_code=None, context=None):
        self._raise_missing_value('power_price')

    def get_social_bonus(self, cr, uid, when_date, tariff_code=None, context=None):
        self._raise_missing_value('social_bonus')

    def get_meter_charge(self, cr, uid, when_date, tariff_code=None, context=None):
        self._raise_missing_value('meter_charge')


SomSimulacioErpAdapter()
