# -*- coding: utf-8 -*-
from osv import osv, fields
from enerdata.calendars import REECalendar
from datetime import datetime


class SomCrawlersHoliday(osv.osv):

    _name = "som.crawlers.holiday"
    _order = "date desc"

    def is_working_day(self, cursor, uid, date):
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        sch_obj = self.pool.get("som.crawlers.holiday")
        ree_calendar = REECalendar()

        return (
            ree_calendar.is_working_day(datetime.strptime(date, "%Y-%m-%d"))
            and datetime.strptime(date, "%Y-%m-%d").weekday() in [0, 1, 2, 3, 4]
            and not self.search(cursor, uid, [("date", "=", date)])
        )

    def is_leaving_day(self, cursor, uid, date):
        return not self.is_working_day(cursor, uid, date)

    _columns = {
        "description": fields.char("Descripcio", size=100),
        "date": fields.date("Data"),
    }


SomCrawlersHoliday()
