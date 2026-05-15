# -*- coding: utf-8 -*-
from osv import osv, fields


class SomSimulacioAnnualCoeff(osv.osv):
    _name = 'som.simulacio.annual.coeff'
    _description = 'Indexed annual coefficients by period'

    _columns = {
        'name': fields.char('Description', size=128, required=True),
        'year': fields.integer('Year', required=True),
        'period': fields.char('Period', size=8, required=True),
        'tariff_code': fields.char('Tariff code', size=16),
        'ratio': fields.float('Ratio', digits=(16, 6), required=True),
        'date_from': fields.date('Valid from'),
        'date_to': fields.date('Valid to'),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': lambda *a: True,
    }

    _sql_constraints = [
        (
            'uniq_annual_tariff_period',
            'unique(year, period, tariff_code)',
            'Annual coefficient already exists for this year/period/tariff.'
        )
    ]


SomSimulacioAnnualCoeff()
