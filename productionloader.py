# -*- coding: utf-8 -*-

from osv import osv, fields
import netsvc
from .erpwrapper import ErpWrapper
from .remainder import RemainderProvider
from mongodb_backend.mongodb2 import mdbpool
from generationkwh.productionloader import ProductionLoader
from generationkwh.sharescurve import PlantSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.isodates import localisodate

class ProductionAggregatorProvider(ErpWrapper):
    def __init__(self, erp, cursor, uid, pid, context=None):
        self.pid = pid
        super(ProductionAggregatorProvider, self).__init__(erp, cursor, uid, context)

    def getWh(self, start, end):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.getWh(self.cursor, self.uid,
                self.pid, start, end, context=self.context)

    def updateWh(self, start, end):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.updateWh(self.cursor, self.uid,
                self.pid, start, end, context=self.context)

    def getFirstMeasurementDate(self):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.firstMeasurementDate(self.cursor, self.uid,
                self.pid, context=self.context)

    def getLastMeasurementDate(self):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.lastMeasurementDate(self.cursor, self.uid,
                self.pid, context=self.context)

    def getNshares(self, pid):
        production=self.erp.pool.get('generationkwh.production.aggregator')
        return production.getNshares(self.cursor, self.uid,
                pid, context=self.context)


class GenerationkWhProductionLoader(osv.osv):

    _name = 'generationkwh.production.loader'
    _auto = False

    def _createProductionLoader(self, cursor, uid, pid, context):
        production = ProductionAggregatorProvider(self, cursor, uid, pid, context)
        nshares = production.getNshares(pid)
        shares = PlantSharesCurve(nshares)
        rights = RightsPerShare(mdbpool.get_db())
        remainders = RemainderProvider(self, cursor, uid, context)

        return ProductionLoader(
                productionAggregator=production,
                plantShareCurver=shares,
                rightsPerShare=rights,
                remainders=remainders)

    def computeAvailableRights(self, cursor, uid, pid, context=None):
        logger = netsvc.Logger()
        productionLoader = self._createProductionLoader(cursor, uid, pid, context)
        productionLoader.computeAvailableRights()

        logger.notifyChannel('gkwh_productionLoader COMPUTE', netsvc.LOG_INFO,
                'Compute available rights')

    def retrieveMeasuresFromPlants(self, cursor, uid, pid, start, end, context=None):
        logger = netsvc.Logger()
        productionLoader = self._createProductionLoader(cursor, uid, pid, context)
        productionLoader.retrieveMeasuresFromPlants(localisodate(start), localisodate(end))

        logger.notifyChannel('gkwh_productionLoader UPDATE', netsvc.LOG_INFO,
                'Retrieve measurements from plant')

GenerationkWhProductionLoader()


