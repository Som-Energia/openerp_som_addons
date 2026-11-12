# -*- coding: utf-8 -*-
from generationkwh.fareperiodcurve import FarePeriodCurve, libfacturacioatr
from som_generationkwh.holidays import HolidaysProvider
from destral import testing
from destral.transaction import Transaction
from yamlns import namespace as ns
from generationkwh.isodates import isodate
import netsvc
import time
import datetime

class HolidaysProvidersMockup(object):
    def get(self, start, stop):
        return self.holidays

    def set(self, holidays):
        self.holidays = [isodate(holiday) for holiday in holidays]

    def __init__(self, holidays=[]):
        self.set(holidays)


class FarePeriodCurveTests(testing.OOTestCase):

    from yamlns.testutils import assertNsEqual

    def setUp(self):
        self.maxDiff = None
        self.pool = self.openerp.pool
        # self.txn = Transaction().start(self.database)

    def tearDown(self):
        # self.txn.stop()
        pass

    def setupCurve(self, start_date, end_date, fare, period, holidays=[]):
        self.maxDiff = None
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup(holidays)
        )
        return p.periodMask(fare, period, isodate(start_date), isodate(end_date))

    def assertArrayEqual(self, result, expected):
        result = list(result)
        result = [result[i:i+25] for i in xrange(0, len(result), 25)]
        expected = [expected[i:i+25] for i in xrange(0, len(expected), 25)]
        return self.assertEqual(result, expected)

    def test__get_class_by_code(self):
        import libfacturacioatr.tarifes as tarifes
        for code, clss in [
            ('2.0A', tarifes.Tarifa20A),
            ('3.0A', tarifes.Tarifa30A),
            ('3.1A', tarifes.Tarifa31A),
            ('2.0DHA', tarifes.Tarifa20DHA),
            ('2.0TD', tarifes.Tarifa20TD),
            ('2.0TDA', tarifes.Tarifa20TDA),
            ('3.0TD', tarifes.Tarifa30TD),
            ('3.0TDA', tarifes.Tarifa30TDA),
            ('6.1TD', tarifes.Tarifa61TD),
            ('6.2TD', tarifes.Tarifa62TD),
            ('6.3TD', tarifes.Tarifa63TD),
            ('6.4TD', tarifes.Tarifa64TD),
            ('6.1TDA', tarifes.Tarifa61TDA),
            ('6.2TDA', tarifes.Tarifa62TDA),
            ('6.3TDA', tarifes.Tarifa63TDA),
            ('6.4TDA', tarifes.Tarifa64TDA),
        ]:
            self.assertEqual(
                tarifes.Tarifa.get_class_by_code(code), clss)

        with self.assertRaises(KeyError):
            tarifes.Tarifa.get_class_by_code("Bad")

    def test_get_class_by_code_fromPool(self):
        import libfacturacioatr.pool.tarifes as tarifespool
        for code, clss in [
            ('2.0A', tarifespool.Tarifa20APool),
            ('3.0A', tarifespool.Tarifa30APool),
            ('3.1A', tarifespool.Tarifa31APool),
            ('2.0DHA', tarifespool.Tarifa20DHAPool),
            ('2.0TD', tarifespool.Tarifa20TDPool),
            # ('2.0TDA', tarifespool.Tarifa20TDAPool),
            ('3.0TD', tarifespool.Tarifa30TDPool),
            # ('3.0TDA', tarifespool.Tarifa30TDAPool),
            ('6.1TD', tarifespool.Tarifa61TDPool),
            ('6.2TD', tarifespool.Tarifa62TDPool),
            ('6.3TD', tarifespool.Tarifa63TDPool),
            ('6.4TD', tarifespool.Tarifa64TDPool),
            # ('6.1TDA', tarifespool.Tarifa61TDAPool),
            # ('6.2TDA', tarifespool.Tarifa62TDAPool),
            # ('6.3TDA', tarifespool.Tarifa63TDAPool),
            # ('6.4TDA', tarifespool.Tarifa64TDAPool),
        ]:
            self.assertEqual(
                tarifespool.TarifaPool.get_class_by_code(code), clss)

        with self.assertRaises(KeyError):
            tarifespool.TarifaPool.get_class_by_code("Bad")

    def test__20A_singleMonth(self):
        mask = self.setupCurve('2015-12-01', '2015-12-31', '2.0A', 'P1')

        self.assertArrayEqual(mask,
                              + 31 * ([1]*24 + [0])
                              )

    def test_20DHA_singleMonth_summer(self):
        mask = self.setupCurve('2015-08-01', '2015-08-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
                              + 31 * ([1]*13+[0]*10+[1, 0])
                              )

    def test_20DHA_singleMonth_winter(self):

        mask = self.setupCurve('2015-12-01', '2015-12-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
                              + 31 * ([1]*12+[0]*10+[1, 1, 0])
                              )

    def test_20DHA_singleMonth_summerToWinter(self):

        mask = self.setupCurve('2016-10-01', '2016-10-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
            + 29 * ( [1]*13+[0]*10+[1,0] )
            +  1 * ( [1]*13+[0]*10+[1,1] )
            +  1 * ( [1]*12+[0]*10+[1,1,0] )
            )

    def test_20DHA_singleMonth_winterToSummer(self):

        mask = self.setupCurve('2016-03-01', '2016-03-31', '2.0DHA', 'P2')

        self.assertArrayEqual(mask,
            + 26 * ( [1]*12+[0]*10+[1,1,0] )
            +  1 * ( [1]*12+[0]*10+[1,0,0] )
            +  4 * ( [1]*13+[0]*10+[1,0] )
            )


    def test_31A_P1_singleMonth(self):

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.1A', 'P1')

        self.assertArrayEqual(mask,
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            )

    def test_31A_P3_singleMonth(self):

        mask = self.setupCurve('2015-12-01', '2015-12-31', '3.1A', 'P3')

        self.assertArrayEqual(mask,
            + 4 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 5 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 5 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 5 * ( [1]*8 + [0]*17 )
            + 2 * ( [1]*18 + [0]*7 )
            + 4 * ( [1]*8 + [0]*17 )
            )

    def test_31A_P1_singleMonth_withHolidays(self):

        mask =self.setupCurve('2015-12-01', '2015-12-31', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 3 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            )

    def test_30A_P1_singleMonth_withHolidays_asWorkingP1AndP4Aggregated(self):

        mask =self.setupCurve('2015-12-01', '2015-12-31', '3.0A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 6 * ( [0]*18 + [1]*4+ [0]*3 )
            + 7 * ( [0]*18 + [1]*4+ [0]*3 )
            + 7 * ( [0]*18 + [1]*4+ [0]*3 )
            + 7 * ( [0]*18 + [1]*4+ [0]*3 ) # Christmasts
            + 4 * ( [0]*18 + [1]*4+ [0]*3 )
            )

    def test_31A_P1_startedMonth(self):

        mask = self.setupCurve('2015-12-7', '2015-12-31', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 3 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 )
            )

    def test_31A_P1_partialMonth(self):
        mask = self.setupCurve('2015-12-7', '2015-12-27', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 3 * ( [0]*25 )
            )

    def test_31A_P1_singleDay(self):
        mask = self.setupCurve('2015-12-25', '2015-12-25', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 1 * ( [0]*25 )
            )

    def test_31A_P1_accrossMonths(self):

        mask = self.setupCurve('2015-11-25', '2015-12-25', '3.1A', 'P1', ['2015-12-25'])

        self.assertArrayEqual(mask,
            + 3 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 5 * ( [0]*17 + [1]*6+ [0]*2 )
            + 2 * ( [0]*25 )
            + 4 * ( [0]*17 + [1]*6+ [0]*2 ) # Christmasts
            + 1 * ( [0]*25 )
            )

#TESTOS NNPP
    def test_20TD_singleDay_workday_weekend_P1(self):

        mask = self.setupCurve('2021-06-04', '2021-06-05', '2.0TD', 'P1')

        self.assertArrayEqual(mask,
                              ([0]*10+[1]*4+[0]*4+[1]*4+[0]*2+[0]) + ([0]*25)
                              )

    def test_20TD_singleDay_workday_weekend_P2(self):

        mask = self.setupCurve('2021-06-04', '2021-06-05', '2.0TD', 'P2')

        self.assertArrayEqual(mask,
                              ([0]*8+[1]*2+[0]*4+[1]*4+[0]*4+[1]*2+[0]) + ([0]*25)
                              )

    def test_20TD_singleDay_workday_weekend_P3(self):

        mask = self.setupCurve('2021-06-04', '2021-06-05', '2.0TD', 'P3')

        self.assertArrayEqual(mask,
                              ([1]*8+[0]*17) + ([1]*24+[0])
                              )

    def test_20TD_singleMonth_summerToWinter_P3(self):

        mask = self.setupCurve('2021-10-01', '2021-10-31', '2.0TD', 'P3')

        self.assertArrayEqual(mask,
            + 1 * ([1]*8+[0]*17)
            + 2 * ([1]*24+[0])
            + 3 * (
                5*([1]*8+[0]*17)
                + 2*([1]*24+[0])
                )
            + 5 * ([1]*8+[0]*17)
            + 1 * ([1]*24+[0]) #hour change: 3am = 2am
            + 1 * ([1]*25)
            )

    def test_20TD_singleMonth_winterToSummer_P3(self):

        mask = self.setupCurve('2022-03-01', '2022-03-31', '2.0TD', 'P3')

        self.assertArrayEqual(mask,
            + 4 * (([1]*8+[0]*17))
            + 2 * ([1]*24+[0])
            + 2 * (
                5*([1]*8+[0]*17)
                + 2*([1]*24+[0])
                )
            + 5 * ([1]*8+[0]*17)
            + 1 * ([1]*24+[0])
            + 1 * ([1]*23+2*[0]) #hour change: 2am = 3am
            + 4 * ([1]*8+[0]*17)
        )

    def test_20TD_singleMonth_winterToSummer_P1(self):

        mask = self.setupCurve('2022-03-01', '2022-03-31', '2.0TD', 'P1')
        weekday = ([0]*10+[1]*4+[0]*4+[1]*4+[0]*2+[0])
        weekend = ([0]*25)
        self.assertArrayEqual(mask,
            + 4 * weekday + 2 * weekend
            + 3 * (5 * weekday + 2 * weekend)
            + 4 * weekday
        )

    def test_20TD_singleMonth_with_holidays(self):

        holidays = ['2021-12-06', '2021-12-08', '2021-12-25']
        mask = self.setupCurve('2021-12-01', '2021-12-31', '2.0TD', 'P3', holidays)
        weekday = ([1]*8 + [0]*17)
        weekend = ([1]*24 + [0])
        self.assertArrayEqual(mask,
            + 3*weekday
            + 3*weekend + 1*weekday + 1*weekend + 2*weekday
            + 3*(2*weekend + 5*weekday)
        )

    def test_30TD_eletricSeasonChange(self):

        mask = self.setupCurve('2022-02-14', '2022-03-13', '3.0TD', 'P2')
        weekday_high = (8*[0] + [1] + 5*[0] + 4*[1] + 4*[0]+ 2*[1] + [0])
        weekday_midhigh = (9*[0] + 5*[1] + 4*[0] + 4*[1] + 3*[0])
        weekend = (25*[0])

        self.assertArrayEqual(mask,
            + 2 * (5 * weekday_high + 2 * weekend)
            + weekday_high
            + 4 * weekday_midhigh + 2*weekend
            + 5 * weekday_midhigh + 2*weekend
        )

    def test_61TD_eletricSeasonChange_lowToMidHigh(self):

        mask = self.setupCurve('2022-10-17', '2022-11-13', '6.1TD', 'P4', ['2022-11-01'])
        weekday_low = (9*[0] + 5*[1] + 4*[0] + 4*[1] + 3*[0])
        other_periods = (25*[0])

        self.assertArrayEqual(mask,
            + 2 * (5 * weekday_low + 2 * other_periods) + weekday_low
            + 13 * other_periods
        )

    def test_equivalentIntervalsForTDFares__endBeforeNewFares(self):
        from dateutil.relativedelta import relativedelta
        start = datetime.date(2019,6,1)
        end = datetime.date(2020,6,8)
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup([])
        )
        result = p.equivalentIntervalsForTDFares(start, end)
        self.assertEqual(result, [(start+ relativedelta(years=+1), end+ relativedelta(years=+1))])

    def test_equivalentIntervalsForTDFares__startAfterNewFares(self):
        start = datetime.date(2021,10,1)
        end = datetime.date(2022,10,8)
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup([])
        )
        result = p.equivalentIntervalsForTDFares(start, end)
        self.assertEqual(result, [(start, end)])

    def test_equivalentIntervalsForTDFares__startBeforeEndAfterNewFares(self):
        start = datetime.date(2020,6,1)
        end = datetime.date(2021,6,8)
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup([])
        )
        result = p.equivalentIntervalsForTDFares(start, end)

        expected = [
            (datetime.date(2021,6,1), datetime.date(2022,5,31)),
            (datetime.date(2021,6,1), datetime.date(2021,6,8)),
                ]
        self.assertEqual(result, expected)

    def test_equivalentIntervalsForTDFares__onlyOneDayBeforeNewFares(self):
        start = datetime.date(2021,5,31)
        end = datetime.date(2022,6,8)
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup([])
        )
        result = p.equivalentIntervalsForTDFares(start, end)

        expected = [
            (datetime.date(2022,5,31), datetime.date(2022,5,31)),
            (datetime.date(2021,6,1), datetime.date(2022,6,8)),
                ]
        self.assertEqual(result, expected)

    def test_equivalentIntervalsForTDFares__sameDayNewFares(self):
        start = datetime.date(2021,6,1)
        end = datetime.date(2022,6,8)
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup([])
        )
        result = p.equivalentIntervalsForTDFares(start, end)

        expected = [
            (datetime.date(2021,6,1), datetime.date(2022,6,8)),
                ]
        self.assertEqual(result, expected)

    def test_equivalentIntervalsForTDFares__endSameDayNewFares(self):
        start = datetime.date(2020,6,1)
        end = datetime.date(2021,6,1)
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup([])
        )
        result = p.equivalentIntervalsForTDFares(start, end)

        expected = [
            (datetime.date(2021,6,1), datetime.date(2022,5,31)),
            (datetime.date(2021,6,1), datetime.date(2021,6,1)),
                ]
        self.assertEqual(result, expected)

        self.assertEqual(result, expected)

    def test_equivalentIntervalsForTDFares__fullIntervalBeforeTD(self):
        start = datetime.date(2020,6,1)
        end = datetime.date(2021,5,31)
        p = FarePeriodCurve(
            holidays=HolidaysProvidersMockup([])
        )
        result = p.equivalentIntervalsForTDFares(start, end)

        expected = [
            (datetime.date(2021,6,1), datetime.date(2022,5,31)),
                ]
        self.assertEqual(result, expected)

    def test_holidaysProvider__implementation(self):
        """
        Test that the holidays provider mockup works as expected.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            holidays_provider = HolidaysProvider(self.openerp, cursor, uid)
            holidays = holidays_provider.get(datetime.date(2024, 8, 15), datetime.date(2025, 5, 1))
            self.assertEqual(
                holidays,
                [
                    isodate('2024-08-15'),
                    isodate('2024-10-12'),
                    isodate('2024-11-01'),
                    isodate('2024-12-06'),
                    isodate('2024-12-08'),
                    isodate('2024-12-25'),
                    isodate('2025-01-01'),
                    isodate('2025-01-06'),
                    isodate('2025-05-01'),
                ]
            )

# vim: et ts=4 sw=4
