# -*- coding: utf-8 -*-
import os
import unittest
import datetime
from yamlns import namespace as ns
dbconfig = None
try:
    import dbconfig
    import erppeek_wst
except ImportError:
    pass
from generationkwh.isodates import (
    addDays,
    isodate,
    )
from somutils.testutils import destructiveTest

def datespan(startDate, endDate, delta=datetime.timedelta(hours=1)):
    currentDate = startDate
    while currentDate < endDate:
        yield currentDate
        currentDate += delta

@unittest.skipIf(not dbconfig, "depends on ERP")
@destructiveTest
class RightsGranter_Test(unittest.TestCase):
    from plantmeter.testutils import assertNsEqual
    def setUp(self):
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Plant = self.erp.GenerationkwhProductionPlant
        self.Meter = self.erp.GenerationkwhProductionMeter
        self.Aggregator = self.erp.GenerationkwhProductionAggregator
        self.AggregatorTestHelper = self.erp.GenerationkwhProductionAggregatorTesthelper
        self.RightsGranter = self.erp.GenerationkwhRightsGranter
        self.TestHelper = self.erp.GenerationkwhTesthelper
        self.ProductionHelper = self.erp.GenerationkwhProductionAggregatorTesthelper
        self.setUpAggregator()
        self.clearMongoCollections() # Rights and measurements
        self.setUpTemp()
        self.clearRemainders() # db

    def tearDown(self):
        self.clearAggregator() # db
        self.clearMongoCollections() # Rights and measurements
        self.clearRemainders() # db
        self.clearTemp()
        self.erp.rollback()
        self.erp.close()

    def setUpAggregator(self):
        self.clearAggregator()

    def clearAggregator(self):
        self.Meter.unlink(self.Meter.search([]))
        self.Plant.unlink(self.Plant.search([]))
        self.Aggregator.unlink(self.Aggregator.search([]))

    def clearMongoCollections(self):
        self.collections = [
            'tm_profile',
            'rightspershare',
        ]
        self.TestHelper.clear_mongo_collections(self.collections)

    def setUpTemp(self):
        import tempfile
        self.tempdir = tempfile.mkdtemp()

    def clearTemp(self):
        for filename in os.listdir(self.tempdir):
            os.remove(os.path.join(self.tempdir, filename))
        os.removedirs(self.tempdir)

    def setupPlant(self, aggr_id, plant, nshares):
        return self.Plant.create(dict(
            aggr_id=aggr_id,
            name='myplant%d' % plant,
            description='myplant%d' % plant,
            enabled=True,
            nshares=nshares,
            first_active_date='2014-01-01'))

    def updatePlant(self, plantName, **kwd):
        id = self.Plant.search([('name','=',plantName)])
        self.Plant.write(id, kwd)

    def updateMeter(self, meterName, **kwd):
        id = self.Meter.search([('name','=',meterName)])
        self.Meter.write(id, kwd)
        from yamlns import namespace as ns
        print self.Meter.read(id,[])


    def setupMeter(self, plant_id, plant, meter):
        return self.Meter.create(dict(
            plant_id=plant_id,
            name='mymeter%d%d' % (plant, meter),
            description='mymeter%d%d' % (plant, meter),
            enabled=True))

    def setupAggregator(self, nplants, nmeters, nshares):
        aggr = self.Aggregator.create(dict(
            name='GenerationkWh',
            description='myaggr',
            enabled=True))

        for plant in range(nplants):
            plant_id = self.setupPlant(aggr, plant, nshares[plant])
            for meter in range(nmeters):
                self.setupMeter(plant_id, plant, meter)
        return aggr

    def setupRemainders(self, remainders):
        remainder = self.erp.model('generationkwh.remainder.testhelper')
        remainder.updateRemainders(remainders)
        return remainder

    def clearRemainders(self):
        remainder = self.erp.model('generationkwh.remainder')
        remainder.clean()

    def setupLocalMeter(self, name, points):
        for start, values in points:
            self.ProductionHelper.fillMeasurements(start, name, values)

    def getProduction(self, aggr_id, start, end):
        return self.AggregatorTestHelper.get_kwh(aggr_id, start, end)

    def test_computeAvailableRights_singleDay(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[1]).read(['id'])['id']
        self.setupLocalMeter('mymeter00',[
            ('2015-08-16', 18*[0]+[1000]+6*[0])
            ])
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.RightsGranter.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1, '2015-08-16', '2015-08-16')
        self.assertEqual(result, +18*[0]+[1000]+6*[0])
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-17', 0],
            ])

    def test_computeAvailableRights_withManyPlantShares_divides(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[4]).read(['id'])['id']
        self.setupLocalMeter('mymeter00',[
            ('2015-08-16', 18*[0]+[20000]+6*[0])
            ])
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.RightsGranter.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1,'2015-08-16','2015-08-16')
        self.assertEqual(result, +18*[0]+[5000]+6*[0])
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-17', 0],
            ])

    def test_computeAvailableRights_withManyPlantShares_twoDays(self):
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[4]).read(['id'])['id']
        self.setupLocalMeter('mymeter00',[
            ('2015-08-16', 18*[0]+[20000]+6*[0]),
            ('2015-08-17', 18*[0]+[20000]+6*[0]),
            ])
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.RightsGranter.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1,'2015-08-16','2015-08-17')
        self.assertEqual(result, 2*(18*[0]+[5000]+6*[0]))
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-18', 0],
            ])

    def test_computeAvailableRights_withManyPlants_dividesByTotalShares(self):
        aggr_id = self.setupAggregator(
                nplants=2,
                nmeters=1,
                nshares=[2,2]).read(['id'])['id']
        self.setupLocalMeter('mymeter00',[
            ('2015-08-16', 18*[0]+[4000]+6*[0])
            ])
        self.setupLocalMeter('mymeter10',[
            ('2015-08-16', 18*[0]+[16000]+6*[0])
            ])
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.RightsGranter.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1,'2015-08-16','2015-08-16')
        self.assertEqual(result, +18*[0]+[5000]+6*[0])
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-17', 0],
            ])

    def test_computeAvailableRights_plantsEnteringLater(self):
        aggr_id = self.setupAggregator(
                nplants=2,
                nmeters=1,
                nshares=[1,3]).read(['id'])['id']
        self.updatePlant('myplant0', first_active_date='2014-01-01')
        #self.updateMeter('mymeter00', first_active_date='2014-01-01')
        self.updatePlant('myplant1', first_active_date='2015-08-17')
        self.updateMeter('mymeter10', first_active_date='2015-08-17')

        self.setupLocalMeter('mymeter00',[
            ('2015-08-16', 18*[0]+[4000]+6*[0]),
            ('2015-08-17', 18*[0]+[4000]+6*[0]),
            ])
        self.setupLocalMeter('mymeter10',[
            ('2015-08-16', 18*[0]+[16000]+6*[0]),
            ('2015-08-17', 18*[0]+[16000]+6*[0]),
            ])
        remainder = self.setupRemainders([(1,'2015-08-16',0)])

        self.RightsGranter.computeAvailableRights(aggr_id)

        result = self.TestHelper.rights_per_share(1,'2015-08-16','2015-08-17')
        self.assertEqual(result,
            +18*[0]+[4000]+6*[0] # from 1sh*(4000kwh+0kwh)/(1sh+0sh) = 4000kwh
            +18*[0]+[5000]+6*[0]  # from 1sh*(4000kwh+16000)/(1sh+4sh) = 5000kwh
        )
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2015-08-18', 0],
            ])


    def test_recomputeRights_singleDay(self):
        self.maxDiff=None
        remainder = self.setupRemainders([])
        aggr_id = self.setupAggregator(
                nplants=1,
                nmeters=1,
                nshares=[10]).read(['id'])['id']
        self.setupLocalMeter('mymeter00',[
            ('2016-08-16', +24*[50]+[0]), # Same
            ('2016-08-17', +24*[60]+[0]), # Higher
            ('2016-08-18', +24*[40]+[0]), # Lower
            ('2016-08-19', +23*[70]+[35]+[0]), # Higher after lower
            ])
        self.TestHelper.setup_rights_per_share(
            1, '2016-08-16', 4*(24*[5]+[0]))

        self.RightsGranter.recomputeRights(aggr_id, '2016-08-16', '2016-08-19')

        result = self.TestHelper.rights_per_share(1, '2016-08-16', '2016-08-19')
        self.assertEqual(result, 
            +24*[5]+[0] # Same
            +24*[6]+[0] # Higher
            +24*[5]+[0] # Lower
            +12*[5]+11*[7]+[5]+[0] # Higher after lower
            )
        result = self.TestHelper.rights_correction(1, '2016-08-16', '2016-08-19')
        self.assertEqual(result,
            +24*[0]+[0] # Same
            +24*[0]+[0] # Higher
            +24*[1]+[0] # Lower
            +12*[-2]+11*[0]+[2]+[0] # Higher after lower
            )
        self.assertEqual(remainder.lastRemainders(), [
            [1, '2016-08-20', -1500],
            ])


unittest.TestCase.__str__ = unittest.TestCase.id

if __name__ == '__main__':
    unittest.main()


# vim: ts=4 sw=4 et
