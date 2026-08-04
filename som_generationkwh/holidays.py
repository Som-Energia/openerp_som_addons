# -*- coding: utf-8 -*-

from .erpwrapper import ErpWrapper
from osv import osv, fields
from enerdata.calendars import REECalendar
from datetime import timedelta

class HolidaysProvider(ErpWrapper):
    # Now it don't use anything from ERP, but we keep the mother class
    # and parameters to don't break the interface.

    def __init__(self, erp, cursor, uid, context=None):
        super(HolidaysProvider, self).__init__(erp, cursor, uid, context)
        self.cal = REECalendar()

    def get(self, start, stop):
        """Returns the holidays to be considering by fares
        between start and stop date including both.
        """
        holidays = []

        day = start
        while day <= stop:
            if self.cal.is_holiday(day):
                holidays.append(day)
            day += timedelta(days=1)

        return holidays


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


