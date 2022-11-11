# -*- coding: utf-8 -*-
from osv import osv, fields


class SomCrawlersHoliday(osv.osv):

    _name = 'som.crawlers.holiday'
    _order = 'date desc'


    def is_working_day(self, cursor, uid, date):
        res = self.search(cursor, uid, [('date','=',date)])
        return not res

    def is_leaving_day(self, cursor, uid, date):
        res = self.search(cursor, uid, [('date','=',date)])
        return res

    _columns = {
        'description': fields.char('Descripcio', size=100),
        'date': fields.date('Data'),
    }

SomCrawlersHoliday()