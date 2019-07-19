#!/usr/bin/env python

import datetime
from generationkwh.isodates import naiveisodate

import unittest

dbconfig = None
try:
    import dbconfig
    import erppeek_wst
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class Holidays_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.c = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.c.begin()
        self.HolidaysHelper = self.c.GenerationkwhHolidaysTesthelper

    def tearDown(self):
        self.c.rollback()
        self.c.close()

    def assertEqualDates(self, result, expected):
        self.assertEqual(expected, result)

    def test_holidays(self):
        self.assertEqualDates(
            self.HolidaysHelper.holidays("2015-12-25", "2015-12-25"),
            [
                '2015-12-25',
            ])

    def test_holidays_severalDays(self):
        self.assertEqualDates(
            self.HolidaysHelper.holidays("2015-12-25", "2016-01-01"),
            [
                '2015-12-25',
                '2016-01-01',
            ])

if __name__=='__main__':
	unittest.TestCase.__str__ = unittest.TestCase.id
	unittest.main()

 
