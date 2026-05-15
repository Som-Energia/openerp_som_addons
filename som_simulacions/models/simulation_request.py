# -*- coding: utf-8 -*-
from osv import osv, fields


class SomSimulacioRequest(osv.osv):
    _name = 'som.simulacio.request'
    _description = 'Indexed estimate simulation request'

    _columns = {
        'name': fields.char('Reference', size=64, required=True),
        'year': fields.integer('Year', required=True),
        'month': fields.integer('Month', required=True),
        'tariff_code': fields.char('Tariff code', size=16, required=True),
        'power_p1': fields.float('Power P1', digits=(16, 6)),
        'power_p2': fields.float('Power P2', digits=(16, 6)),
        'power_p3': fields.float('Power P3', digits=(16, 6)),
        'result_ids': fields.one2many('som.simulacio.result', 'request_id', 'Results'),
    }


SomSimulacioRequest()
