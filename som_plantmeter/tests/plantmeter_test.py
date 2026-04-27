#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime, timedelta
from somutils.isodates import localisodate, parseLocalTime, asUtc
from plantmeter.testutils import destructiveTest
from yamlns import namespace as ns
from destral import testing
from destral.transaction import Transaction
import tempfile


def localTime(string):
    isSummer = string.endswith("S")
    if isSummer:
        string = string[:-1]
    return parseLocalTime(string, isSummer)


def datespan(startDate, endDate):
    delta = timedelta(hours=1)
    currentDate = startDate
    while currentDate < endDate:
        yield currentDate
        currentDate += delta


class PlantShareProvider_Test(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.maxDiff = None
        self.Mix = self.openerp.pool.get('generationkwh.production.aggregator')
        self.Plant = self.openerp.pool.get('generationkwh.production.plant')
        self.Meter = self.openerp.pool.get('generationkwh.production.meter')
        self.helper = self.openerp.pool.get(
            'generationkwh.production.aggregator.testhelper')

    def tearDown(self):
        self.txn.stop()

    from plantmeter.testutils import assertNsEqual

    def setupMix(self, name, plants=[], description=None, enabled=True):

        mix_id = self.Mix.create(self.cursor, self.uid, dict(
            name=name,
            description=description or name+' description',
            enabled=enabled,
        ))

        return mix_id, [
            self.Plant.create(self.cursor, self.uid, dict(
                plant,
                aggr_id=mix_id,
                description=plant['name']+' description',
                enabled=True,
            ))
            for plantIndex, plant in enumerate(plants)
        ]

    def test_items_withZeroPlants(self):
        self.setupMix('testmix', [])
        items = self.helper.plantShareItems(self.cursor, self.uid, 'testmix')

        self.assertNsEqual(ns(items=items), """
            items: []
        """)

    def test_items_withOnePlant(self):
        self.setupMix('testmix', [
            dict(
                name='plant1',
                nshares=10,
                first_active_date='2019-03-02',
                last_active_date='2019-03-03',
                meters=[]
            ),
        ])
        items = self.helper.plantShareItems(self.cursor, self.uid, 'testmix')

        self.assertNsEqual(ns(items=items), """
            items:
            - mix: testmix
              shares: 10
              firstEffectiveDate: '2019-03-02'
              lastEffectiveDate: '2019-03-03'
        """)

    def test_items_withManyPlant(self):
        self.setupMix('testmix', [
            dict(
                name='plant1',
                nshares=10,
                first_active_date='2019-03-02',
                last_active_date='2019-03-03',
                meters=[]
            ),
            dict(
                name='plant2',
                nshares=20,
                first_active_date='2019-02-02',
                last_active_date='2019-02-03',
                meters=[]
            ),
        ])
        items = self.helper.plantShareItems(self.cursor, self.uid, 'testmix')

        self.assertNsEqual(ns(items=items), """
            items:
            - mix: testmix
              shares: 10
              firstEffectiveDate: '2019-03-02'
              lastEffectiveDate: '2019-03-03'
            - mix: testmix
              shares: 20
              firstEffectiveDate: '2019-02-02'
              lastEffectiveDate: '2019-02-03'
        """)

    def test_items_filtersOtherMixes(self):
        self.setupMix('testmix', [
            dict(
                name='plant1',
                nshares=10,
                first_active_date='2019-03-02',
                last_active_date='2019-03-03',
                meters=[]
            ),
        ])
        self.setupMix('othermix', [
            dict(
                name='plant2',
                nshares=20,
                first_active_date='2019-02-02',
                last_active_date='2019-02-03',
                meters=[]
            ),
        ])
        items = self.helper.plantShareItems(self.cursor, self.uid, 'testmix')

        self.assertNsEqual(ns(items=items), """
            items:
            - mix: testmix
              shares: 10
              firstEffectiveDate: '2019-03-02'
              lastEffectiveDate: '2019-03-03'
        """)


@destructiveTest
class GenerationkwhProductionAggregator_Test(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.maxDiff = None
        self.collection = 'tm_profile'

        self.helper = self.openerp.pool.get(
            'generationkwh.production.aggregator.testhelper')
        self.aggr_obj = self.openerp.pool.get(
            'generationkwh.production.aggregator')
        self.plant_obj = self.openerp.pool.get(
            'generationkwh.production.plant')
        self.meter_obj = self.openerp.pool.get(
            'generationkwh.production.meter')
        self.tempdir = tempfile.mkdtemp()
        self.clearAggregator()
        self.clearMeasurements()
        self.clearTempContent()

    def tearDown(self):
        self.txn.stop()

    def clear(self):
        self.clearAggregator()
        self.clearMeasurements()
        self.clearTemp()

    def clearAggregator(self):
        self.meter_obj.unlink(self.cursor, self.uid,
                              self.meter_obj.search(self.cursor, self.uid, []))
        self.plant_obj.unlink(self.cursor, self.uid,
                              self.plant_obj.search(self.cursor, self.uid, []))
        self.aggr_obj.unlink(self.cursor, self.uid,
                             self.aggr_obj.search(self.cursor, self.uid, []))

    def clearMeasurements(self):
        self.helper.clear_mongo_collections(self.cursor, self.uid, [
            self.collection,
        ])

    def clearTemp(self):
        self.clearTempContent()
        os.removedirs(self.tempdir)

    def clearTempContent(self):
        for filename in os.listdir(self.tempdir):
            os.remove(os.path.join(self.tempdir, filename))

    def setupAggregator(self, nplants, nmeters):
        aggr_id = self.aggr_obj.create(self.cursor, self.uid, dict(
            name='myaggr',
            description='myaggr',
            enabled=True))

        meters = []
        for plant in range(nplants):
            plant_id = self.setupPlant(aggr_id, plant)
            for meter in range(nmeters):
                meters.append(self.setupMeter(plant_id, plant, meter))
        return (self.aggr_obj.browse(self.cursor, self.uid, aggr_id),
                self.meter_obj.browse(self.cursor, self.uid, meters))

    def setupPlant(self, aggr_id, plant):
        return self.plant_obj.create(self.cursor, self.uid, dict(
            aggr_id=aggr_id,
            name='myplant%d' % plant,
            description='myplant%d' % plant,
            enabled=True,
            first_active_date='2000-01-01',
            nshares=1000*(plant+1)))

    def setupMeter(self, plant_id, plant, meter):
        return self.meter_obj.create(self.cursor, self.uid, dict(
            plant_id=plant_id,
            name='mymeter%d%d' % (plant, meter),
            description='mymeter%d%d' % (plant, meter),
            first_active_date='2000-01-01',
            enabled=True))

    def setupPointsByDay(self, points):
        for meter, start, end, values in points:
            daterange = datespan(
                localisodate(start),
                localisodate(end)+timedelta(days=1)
            )
            for date, value in zip(daterange, values):
                self.helper.fillMeasurementPoint(self.cursor, self.uid,
                                                 str(asUtc(date))[:-6], meter, value)

    def setupPointsByHour(self, points):
        for meter, date, value in points:
            self.helper.fillMeasurementPoint(self.cursor, self.uid,
                                             str(asUtc(localTime(date)))[:-6], meter, value)

    def fillMeter(self, name, points):
        for start, values in points:
            self.helper.fillMeasurements(
                self.cursor, self.uid, start, name, values)

    def setupLocalMeter(self, filename, points):
        filename = os.path.join(self.tempdir, filename)
        import csv

        def toStr(date):
            return date.strftime('%Y-%m-%d %H:%M')

        with open(filename, 'w') as tmpfile:
            writer = csv.writer(tmpfile, delimiter=';')
            writer.writerows([
                (toStr(date), summer, value, 0, 0)
                for start, end, summer, values in points
                for date, value in zip(
                    datespan(
                        datetime.strptime(start, "%Y-%m-%d"),
                        datetime.strptime(end, "%Y-%m-%d")+timedelta(days=1)
                    ), values)
            ])

    def test_get_kwh_onePlant_withNoPoints(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-08-16', '2015-08-16', 24*[10])
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-17', '2015-08-17')
        self.assertEqual(production, 25*[0])

    def test_get_kwh_onePlant_winter(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-03-16', '2015-03-16', 24*[10])
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-03-16', '2015-03-16')
        self.assertEqual(production, 24*[10]+[0])

    def test_get_kwh_onePlant_winterToSummer(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByHour([
            ('mymeter00', '2015-03-29 00:00:00', 1),
            ('mymeter00', '2015-03-29 01:00:00', 2),
            ('mymeter00', '2015-03-29 03:00:00', 3),
            ('mymeter00', '2015-03-29 23:00:00', 4)
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-03-29', '2015-03-29')
        self.assertEqual(production, [1, 2, 3]+19*[0]+[4, 0, 0])

    def test_get_kwh_onePlant_summer(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-08-16', '2015-08-16', 24*[10])
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 24*[10]+[0])

    def test_get_kwh_onePlant_summerToWinter(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByHour([
            ('mymeter00', '2015-10-25 00:00:00', 1),
            ('mymeter00', '2015-10-25 02:00:00S', 2),
            ('mymeter00', '2015-10-25 02:00:00', 3),
            ('mymeter00', '2015-10-25 23:00:00', 4)
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-10-25', '2015-10-25')
        self.assertEqual(production, [1, 0, 2, 3]+20*[0]+[4])

    def test_get_kwh_twoPlant_withNoPoints(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-17', '2015-08-17')
        self.assertEqual(production, 25*[0])

    def test_get_kwh_twoPlant_winter(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-03-16', '2015-03-16', 24*[10]),
            ('mymeter10', '2015-03-16', '2015-03-16', 24*[10])
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-03-16', '2015-03-16')
        self.assertEqual(production, 24*[20] + [0])

    def test_get_kwh_twoPlant_winterToSummer(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByHour([
            ('mymeter00', '2015-03-29 00:00:00', 1),
            ('mymeter00', '2015-03-29 01:00:00', 2),
            ('mymeter00', '2015-03-29 03:00:00', 3),
            ('mymeter00', '2015-03-29 23:00:00', 4),
            ('mymeter10', '2015-03-29 00:00:00', 1),
            ('mymeter10', '2015-03-29 01:00:00', 2),
            ('mymeter10', '2015-03-29 03:00:00', 3),
            ('mymeter10', '2015-03-29 23:00:00', 4)
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-03-29', '2015-03-29')
        self.assertEqual(production, [2, 4, 6]+19*[0]+[8, 0, 0])

    def test_get_kwh_twoPlant_summer(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-08-16', '2015-08-16', 24*[10]),
            ('mymeter10', '2015-08-16', '2015-08-16', 24*[10])
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 24*[20]+[0])

    def test_get_kwh_twoPlant_summerToWinter(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByHour([
            ('mymeter00', '2015-10-25 00:00:00', 1),
            ('mymeter00', '2015-10-25 02:00:00S', 2),
            ('mymeter00', '2015-10-25 02:00:00', 3),
            ('mymeter00', '2015-10-25 23:00:00', 4),
            ('mymeter10', '2015-10-25 00:00:00', 1),
            ('mymeter10', '2015-10-25 02:00:00S', 2),
            ('mymeter10', '2015-10-25 02:00:00', 3),
            ('mymeter10', '2015-10-25 23:00:00', 4)
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-10-25', '2015-10-25')
        self.assertEqual(production, [2, 0, 4, 6]+20*[0]+[8])

    def test_get_kwh_twoDays(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        self.setupPointsByDay([
            ('mymeter00', '2015-03-16', '2015-03-17', 48*[10])
        ])
        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-03-16', '2015-03-17')
        self.assertEqual(production, 24*[10]+[0]+24*[10]+[0])

    def test_fillMeter_withNoPoints(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
        ])

        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 25*[0])

    def test_fillMeter_onePlant(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
        ])

        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 10*[0]+14*[10]+[0])

    def test_fillMeter_twoPlant_sameDay(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
        ])
        self.fillMeter('mymeter10', [
            ('2015-08-16', 10*[0]+14*[20]),
        ])

        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 10*[0]+14*[30]+[0])

    def test_fillMeter_twoPlant_differentDays(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
        ])
        self.fillMeter('mymeter10', [
            ('2015-08-17', 10*[0]+14*[20]),
        ])

        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-16', '2015-08-17')
        self.assertEqual(production, 10*[0]+14*[10]+[0]+10*[0]+14*[20]+[0])

    def test_fillMeter_missing(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1,
        )
        aggr_id = aggr.read(['id'])[0]['id']
        meter_id = meters[0].read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
        ])

        production = self.helper.get_kwh(self.cursor, self.uid,
                                         aggr_id, '2015-08-16', '2015-08-16')
        self.assertEqual(production, 10*[0]+14*[10]+[0])

    def test_firstActiveDate_noPlants(self):
        aggr, meters = self.setupAggregator(
            nplants=0,
            nmeters=0)
        aggr_id = aggr.read(['id'])[0]['id']

        date = self.helper.firstActiveDate(self.cursor, self.uid, aggr_id)
        self.assertEqual(date, None)

    def test_firstActiveDate_singlePlant(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']

        date = self.helper.firstActiveDate(self.cursor, self.uid, aggr_id)
        self.assertEqual(date, '2000-01-01')

    def test_firstMeasurementDate_noPoint(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
        ])

        date = self.helper.firstMeasurementDate(self.cursor, self.uid, aggr_id)
        self.assertEqual(date, None)

    def test_firstMeasurementDate_onePlant(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
            ('2015-08-17', 10*[0]+14*[10]),
        ])

        date = self.helper.firstMeasurementDate(self.cursor, self.uid, aggr_id)
        self.assertEqual(date, '2015-08-16')

    def test_firstMeasurementDate_twoPlant(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
        ])
        self.fillMeter('mymeter10', [
            ('2015-08-17', 10*[0]+14*[20]),
        ])

        date = self.helper.firstMeasurementDate(self.cursor, self.uid, aggr_id)
        self.assertEqual(date, '2015-08-16')

    def test_lastMeasurementDate_onePlant(self):
        aggr, meters = self.setupAggregator(
            nplants=1,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
            ('2015-08-17', 10*[0]+14*[10]),
        ])

        date = self.helper.lastMeasurementDate(self.cursor, self.uid, aggr_id)
        self.assertEqual(date, '2015-08-17')

    def test_lastMeasurementDate_twoPlant(self):
        aggr, meters = self.setupAggregator(
            nplants=2,
            nmeters=1)
        aggr_id = aggr.read(['id'])[0]['id']
        self.fillMeter('mymeter00', [
            ('2015-08-16', 10*[0]+14*[10]),
        ])
        self.fillMeter('mymeter10', [
            ('2015-08-17', 10*[0]+14*[20]),
        ])

        date = self.helper.lastMeasurementDate(self.cursor, self.uid, aggr_id)
        self.assertEqual(date, '2015-08-16')


# vim: et ts=4 sw=4
