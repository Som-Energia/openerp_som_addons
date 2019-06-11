# -*- coding: utf-8 -*-

from osv import osv, fields
import netsvc
from .erpwrapper import ErpWrapper
from .remainder import RemainderProvider
from mongodb_backend.mongodb2 import mdbpool
from generationkwh.productionloader import ProductionLoader
from generationkwh.sharescurve import MixTotalSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.isodates import (
    localisodate,
    addDays,
    isodate,
    dateToLocal,
    )
from yamlns import namespace as ns
from som_plantmeter.som_plantmeter import PlantShareProvider


class ProductionAggregatorProvider(ErpWrapper):
    def __init__(self, erp, cursor, uid, pid, context=None):
        self.pid = pid
        super(ProductionAggregatorProvider, self).__init__(erp, cursor, uid, context)

    def get_kwh(self, start, end):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.get_kwh(self.cursor, self.uid,
                self.pid, start, end, context=self.context)

    def getFirstMeasurementDate(self):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.firstMeasurementDate(self.cursor, self.uid,
                self.pid, context=self.context)

    def getLastMeasurementDate(self):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.lastMeasurementDate(self.cursor, self.uid,
                self.pid, context=self.context)

# TODO: Rename it as GenerationkwhRightsCalculator
class GenerationkWhProductionLoader(osv.osv):

    _name = 'generationkwh.production.loader'
    _auto = False

    def _createProductionLoader(self, cursor, uid, pid, context):
        production = ProductionAggregatorProvider(self, cursor, uid, pid, context)
        plantsharesprovider = PlantShareProvider(self, cursor, uid, 'GenerationkWh')
        plantsharecurver = MixTotalSharesCurve(plantsharesprovider)
        rights = RightsPerShare(mdbpool.get_db())
        remainders = RemainderProvider(self, cursor, uid, context)

        return ProductionLoader(
                productionAggregator=production,
                plantShareCurver=plantsharecurver,
                rightsPerShare=rights,
                remainders=remainders)

    def computeAvailableRights(self, cursor, uid, pid, context=None):
        logger = netsvc.Logger()
        productionLoader = self._createProductionLoader(cursor, uid, pid, context)
        log = productionLoader.computeAvailableRights()

        logger.notifyChannel('gkwh_productionLoader COMPUTE', netsvc.LOG_INFO,
                'Compute available rights')
        return log

    def recomputeRightsOnPeriod(self, cursor, uid, pid,
            firstDateToRecompute,
            lastDateToRecompute,
            initialRemainders,
            context=None,
        ):
        logger = netsvc.Logger()
        firstDateToRecompute = isodate(firstDateToRecompute)
        lastDateToRecompute = isodate(lastDateToRecompute)
        class RightsRecomputationRemainders:
            def __init__(self, firstDate, sharesToWh):
                self.firstDate = firstDate
                self._input = sharesToWh
                self._outremainders = {}

            def lastRemainders(self):
                return [
                    (r.nshares, self.firstDate, r.remainder_wh)
                    for r in (ns(d) for d in self._input)
                    ]

            def updateRemainders(self, newRemainders):
                for nshares, nextDate, Wh in newRemainders:
                    self._outremainders[nshares] = Wh

            def getOutput(self):
                return self._outremainders


        production = ProductionAggregatorProvider(self, cursor, uid, pid, context)
        plantsharesprovider = PlantShareProvider(self, cursor, uid, 'GenerationkWh')
        plantsharecurver = MixTotalSharesCurve(plantsharesprovider)
        rights = RightsPerShare(mdbpool.get_db())
        remainders = RightsRecomputationRemainders(firstDateToRecompute, initialRemainders)

        productionLoader = ProductionLoader(
                productionAggregator=production,
                plantShareCurver=plantsharecurver,
                rightsPerShare=rights,
                remainders=remainders)
        result=[]
        productionLoader.computeAvailableRights(lastDateToRecompute)

        logger.notifyChannel('gkwh_productionLoader COMPUTE', netsvc.LOG_INFO,
                'Compute available rights')

        result.append( dict(
            nshares = 1,
            first_date = str(firstDateToRecompute),
            last_date = str(lastDateToRecompute),
            next_date = str(addDays(dateToLocal(lastDateToRecompute),1).date()),
            previous_remainder_wh = 0,
            rights_kwh = 15000,
            remainder_wh = 0,
        ))
        return result


GenerationkWhProductionLoader()


