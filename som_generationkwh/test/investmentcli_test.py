#!/usr/bin/env python
# -*- coding: utf-8 -*-

import genkwh_investments as cli
import erppeek_wst
import unittest
import b2btest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass

@unittest.skipIf(not dbconfig, "depends on ERP")
class InvestmentCommand_Test(unittest.TestCase):
    def setUp(self):
        cli.c = erppeek_wst.ClientWST(**dbconfig.erppeek)
        cli.c.begin()
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        cli.clear()

    def tearDown(self):
        cli.c.rollback()
        cli.c.close()

    def test_clean(self):
        data = cli.listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_toEarly(self):
        cli.create(stop="2015-06-29")
        data = cli.listactive(csv=True)
        self.assertEqual(data,'')

    def test_create_onlyFirstBatch(self):
        cli.create(stop="2015-06-30")
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstBatch_twice(self):
        cli.create(stop="2015-06-30")
        cli.create(stop="2015-06-30")
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_firstAndSecondBatch(self):
        cli.create(stop="2015-07-03")
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_justSecondBatch(self):
        cli.create(start='2015-07-02', stop="2015-07-03")
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_waitTwoDays(self):
        cli.create(stop="2015-06-30", waitingDays=2)
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_expireOneYear(self):
        cli.create(stop="2015-06-30", waitingDays=2, expirationYears=1)
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_create_inTwoBatches(self):
        cli.create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        cli.create(stop="2015-07-03")
        data = cli.listactive(csv=True)

    def test_listactive_withMember(self):
        cli.create(stop="2015-06-30")
        data = cli.listactive(csv=True, member=469)
        self.assertMultiLineEqual(data,
            '469\tFalse\tFalse\t3\n'
            '469\tFalse\tFalse\t2\n'
        )

    def test_listactive_withStop_shouldBeFirstBatch(self):
        cli.create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = cli.listactive(csv=True, stop="2015-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStopAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Second batch is not activated, and is not shown even if we extend stop
        cli.create(stop="2015-06-30", waitingDays=0, expirationYears=1)
        cli.create(start="2015-07-03", stop="2015-07-03")
        data = cli.listactive(csv=True, stop="2020-07-03")
        self.assertB2BEqual(data)

    def test_listactive_withStart_excludeExpired_shouldBeSecondBatch(self):
        # Expired contracts do not show if start is specified and it is earlier
        cli.create(stop="2015-07-03", waitingDays=0, expirationYears=1)
        data = cli.listactive(csv=True, start="2016-07-01")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoActivatedInvestments_shouldBeFirstBatch(self):
        # Unactivated contracts are not listed if start is specified
        cli.create(stop="2015-06-30", waitingDays=0, expirationYears=1) # listed
        cli.create(start="2015-07-03", stop="2015-07-03") # unlisted
        data = cli.listactive(csv=True, start="2016-06-30")
        self.assertB2BEqual(data)

    def test_listactive_withStartAndNoExpirationRunForEver_shouldBeSecondBatch(self):
        # Active with no deactivation keeps being active for ever
        cli.create(stop="2015-06-30", waitingDays=0, expirationYears=1) # unlisted
        cli.create(start="2015-07-03", stop="2015-07-03", waitingDays=0) # listed
        data = cli.listactive(csv=True, start="2036-06-30")
        self.assertB2BEqual(data)


    def test_effective_withStop(self):
        cli.create(stop="2015-07-03")
        cli.effective(stop="2015-06-30", waitingDays=0)
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_effective_withStart(self):
        cli.create(stop="2015-07-03")
        cli.effective(start="2015-07-02", waitingDays=0)
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)

    def test_effective_withExpiration(self):
        cli.create(stop="2015-07-03")
        cli.effective(stop="2015-06-30", waitingDays=0, expirationYears=1)
        data = cli.listactive(csv=True)
        self.assertB2BEqual(data)


unittest.TestCase.__str__ = unittest.TestCase.id




