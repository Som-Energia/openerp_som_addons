# -*- coding: utf-8 -*-
import unittest
import datetime
import xmlrpclib
dbconfig = None
try:
    import dbconfig
    import erppeek_wst
except ImportError:
    pass


@unittest.skipIf(not dbconfig, "depends on ERP")
class Remainder_Test(unittest.TestCase):

    def setUp(self):
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Remainder = self.erp.GenerationkwhRemainder
        self.RemainderHelper = self.erp.GenerationkwhRemainderTesthelper
        self.RemainderHelper.clean()

    def setupProvider(self,remainders=[]):
        self.RemainderHelper.updateRemainders(remainders)

    def assertLastEquals(self, expectation):
        result = self.RemainderHelper.lastRemainders()
        self.assertEqual([list(a) for a in expectation], sorted(result))

    def tearDown(self):
        try:
            self.erp.rollback()
            self.erp.close()
        except xmlrpclib.Fault as e:
            if 'transaction block' not in e.faultCode:
                raise

    def test_last_noRemainders(self):
        self.setupProvider()
        self.assertLastEquals([])

    def test_last_oneRemainder(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            ])

    def test_last_manyRemainder(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            ])

    def test_last_manyDates_takesLast(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            (2,'2016-02-25',1),
            (1,'2016-01-24',2),
            (2,'2016-02-27',4),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',3),
            (2,'2016-02-27',4),
            ])

    def test_last_sameDate_lastInsertedPrevails(self):
        self.setupProvider([
            (1,'2016-02-25',1),
            (1,'2016-02-25',2),
            (1,'2016-02-25',3),
            (1,'2016-02-25',4),
            (1,'2016-02-25',5),
            (1,'2016-02-25',6),
            ])
        self.assertLastEquals([
            (1,'2016-02-25',6),
            ])

    # TODO: Does this has sense at all? DGG
    def test_last_sameDateAndNShares_raises(self):
        self.Remainder.create(dict(
            n_shares=1,
            target_day='2016-02-25',
            remainder_wh=1,
        ))
        with self.assertRaises(Exception) as ctx:
            self.Remainder.create(dict(
                n_shares=1,
                target_day='2016-02-25',
                remainder_wh=2,
             ))

        self.assertIn(
            # TODO: at some PG version it shows the simbol instead of the description
            #"Only one remainder of last date computed and "
            #"number of shares is allowed",
            "generationkwh_remainder_unique_n_shares_target_day",
            ctx.exception.faultCode
            )

    def test_newRemaindersToTrack_when1SharesAvailable(self):
        self.setupProvider([
            (1,'2016-02-25',1),
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            (1,'2016-02-25',1),
            (3,'2016-02-25',0),
            ])

    def test_newRemaindersToTrack_when1SharesAvailable_takesOlder(self):
        self.setupProvider([
            (1,'2016-02-25',1),
            (1,'2016-02-28',1),
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            (1,'2016-02-28',1),
            (3,'2016-02-25',0),
            ])

    def test_newRemaindersToTrack_no1Shares_ignores(self):
        self.setupProvider([
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            ])

    def test_newRemaindersToTrack_otherButNo1Shares_ignored(self):
        self.setupProvider([
            (2,'2016-02-25',1),
            ])
        self.Remainder.newRemaindersToTrack([3])
        self.assertLastEquals([
            (2,'2016-02-25',1),
            ])

    def test_newRemaindersToTrack_manyRemindersToTrack(self):
        self.setupProvider([
            (1,'2016-02-25',0),
            ])
        self.Remainder.newRemaindersToTrack([3,6])
        self.assertLastEquals([
            (1,'2016-02-25',0),
            (3,'2016-02-25',0),
            (6,'2016-02-25',0),
            ])

    def assertFilledEqual(self, expectation):
        result = self.Remainder.filled()
        self.assertEqual(expectation, result)

    def test_filled_oneReminder_returnsNothing(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            ])
        self.assertFilledEqual([
            ])

    def test_filled_twoReminder_thatReminder(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            (1,'2016-02-26',2),
            ])
        self.assertFilledEqual([1])

    def test_filled_twoReminder_differentNShares(self):
        self.setupProvider([
            (1,'2016-02-25',3),
            (2,'2016-02-25',3),
            ])
        self.assertFilledEqual([])


if __name__ == '__main__':
    unittest.TestCase.__str__ = unittest.TestCase.id
    unittest.main()

# vim: et sw=4 ts=4
