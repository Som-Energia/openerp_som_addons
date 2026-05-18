# -*- coding: utf-8 -*-
from osv import osv, fields


class SomSimulacioEnergyPriceMonthly(osv.osv):
    _name = 'som.simulacio.energy.price.monthly'
    _description = 'Indexed monthly energy prices'

    _columns = {
        'name': fields.char('Description', size=128, required=True),
        'year': fields.integer('Year', required=True),
        'month': fields.integer('Month', required=True),
        'period': fields.char('Period', size=8, required=True),
        'tariff_code': fields.char('Tariff code', size=16),
        'price': fields.float('Price', digits=(16, 6), required=True),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': lambda *a: True,
    }

    _sql_constraints = [
        (
            'uniq_monthly_tariff_period',
            'unique(year, month, period, tariff_code)',
            'Monthly energy price already exists for this year/month/period/tariff.'
        )
    ]

    def _check_positive_price(self, cr, uid, ids, context=None):
        for row in self.read(cr, uid, ids, ['price'], context=context):
            if (row.get('price') or 0.0) <= 0.0:
                return False
        return True

    _constraints = [
        (
            _check_positive_price,
            'Monthly energy price must be greater than zero.',
            ['price']
        )
    ]


SomSimulacioEnergyPriceMonthly()
