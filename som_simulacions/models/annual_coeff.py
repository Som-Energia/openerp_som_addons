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

    def _check_ratio_range(self, cr, uid, ids, context=None):
        for row in self.read(cr, uid, ids, ['ratio'], context=context):
            ratio = row.get('ratio') or 0.0
            if ratio < 0.0 or ratio > 1.0:
                return False
        return True

    def _check_ratio_sum(self, cr, uid, ids, context=None):
        for row in self.read(cr, uid, ids, ['year', 'tariff_code'], context=context):
            coeff_ids = self.search(cr, uid, [
                ('year', '=', row['year']),
                ('tariff_code', '=', row.get('tariff_code')),
            ], context=context)
            if len(coeff_ids) < 3:
                continue
            rows = self.read(cr, uid, coeff_ids, ['ratio'], context=context)
            total = sum([(r.get('ratio') or 0.0) for r in rows])
            if abs(total - 1.0) > 0.0001:
                return False
        return True

    def _check_no_overlapping_window(self, cr, uid, ids, context=None):
        for row in self.read(cr, uid, ids, [
            'id', 'tariff_code', 'period', 'date_from', 'date_to'
        ], context=context):
            date_from = row.get('date_from')
            date_to = row.get('date_to')
            if not date_from or not date_to:
                continue
            other_ids = self.search(cr, uid, [
                ('id', '!=', row['id']),
                ('tariff_code', '=', row.get('tariff_code')),
                ('period', '=', row.get('period')),
                ('date_from', '<=', date_to),
                ('date_to', '>=', date_from),
            ], context=context)
            if other_ids:
                return False
        return True

    _constraints = [
        (_check_ratio_range, 'Coefficient ratio must be in range [0, 1].', ['ratio']),
        (_check_ratio_sum, 'Coefficient ratios must sum 1.0 (+/- 0.0001).', ['ratio']),
        (
            _check_no_overlapping_window,
            'Coefficient validity windows cannot overlap for same period/tariff.',
            ['date_from', 'date_to', 'period', 'tariff_code']
        ),
    ]


SomSimulacioAnnualCoeff()
