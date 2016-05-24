# -*- coding: utf-8 -*-

from .erpwrapper import ErpWrapper
from osv import osv, fields
from generationkwh.isodates import isodate

class HolidaysProvider(ErpWrapper):

    def get(self, start, stop):
        """Returns the holidays to be considering by fares
        between start and stop date including both.
        """

        Holidays = self.erp.pool.get('giscedata.dfestius')
        ids = Holidays.search(self.cursor, self.uid, [
            ('name', '>=', start),
            ('name', '<=', stop),
            ], 0,None,'name desc',self.context)
        return [
            isodate(h['name'])
            for h in Holidays.read(self.cursor, self.uid,
                ids, ['name'], self.context)
            ]

class GenerationkWhHolidaysTestHelper(osv.osv):
    """
        Helper model that enables accessing data providers
        from tests written with erppeek.
    """

    _name = 'generationkwh.holidays.testhelper'
    _auto = False

    def holidays(self, cursor, uid,
            start, stop,
            context=None):
        holidaysProvider = HolidaysProvider(self, cursor, uid, context)
        return [ str(name) for name in holidaysProvider.get(start, stop) ]

GenerationkWhHolidaysTestHelper()


