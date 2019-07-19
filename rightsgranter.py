# -*- coding: utf-8 -*-

from osv import osv, fields
import netsvc
from mongodb_backend.mongodb2 import mdbpool

from .erpwrapper import ErpWrapper
from .remainder import RemainderProvider
from som_plantmeter.som_plantmeter import PlantShareProvider

from generationkwh.rightsgranter import RightsGranter
from generationkwh.sharescurve import MixTotalSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.rightscorrection import RightsCorrection
from generationkwh.isodates import (
    localisodate,
    addDays,
    isodate,
    dateToLocal,
    )
from yamlns import namespace as ns


class ProductionMixProvider(ErpWrapper):
    def __init__(self, erp, cursor, uid, pid, context=None):
        self.pid = pid
        super(ProductionMixProvider, self).__init__(erp, cursor, uid, context)

    def get_kwh(self, start, end):
        mix=self.erp.pool.get('generationkwh.production.aggregator')
        return mix.get_kwh(self.cursor, self.uid,
                self.pid, start, end, context=self.context)

    def getFirstMeasurementDate(self):
        mix=self.erp.pool.get('generationkwh.production.aggregator')
        return mix.firstMeasurementDate(self.cursor, self.uid,
                self.pid, context=self.context)

    def getLastMeasurementDate(self):
        mix=self.erp.pool.get('generationkwh.production.aggregator')
        return mix.lastMeasurementDate(self.cursor, self.uid,
                self.pid, context=self.context)

class GenerationkWhRightsGranter(osv.osv):

    _name = 'generationkwh.rights.granter'
    _auto = False

    def _createRightsGranter(self, cursor, uid, mix_id, context):
        mix = ProductionMixProvider(self, cursor, uid, mix_id, context)
        plantsharesprovider = PlantShareProvider(self, cursor, uid, 'GenerationkWh')
        plantsharecurver = MixTotalSharesCurve(plantsharesprovider)
        rights = RightsPerShare(mdbpool.get_db())
        rightsCorrection = RightsCorrection(mdbpool.get_db())
        remainders = RemainderProvider(self, cursor, uid, context)

        return RightsGranter(
                productionAggregator=mix,
                plantShareCurver=plantsharecurver,
                rightsPerShare=rights,
                remainders=remainders,
                rightsCorrection=rightsCorrection)

    def computeAvailableRights(self, cursor, uid, mix_id, context=None):
        logger = netsvc.Logger()
        rightsGranter = self._createRightsGranter(cursor, uid, mix_id, context)
        log = rightsGranter.computeAvailableRights()

        logger.notifyChannel('gkwh_rightsgranter COMPUTE', netsvc.LOG_INFO,
                'Compute available rights')
        return log

    def recomputeRights(self, cursor, uid, mix_id, first_date, last_date, context=None):
        logger = netsvc.Logger()
        rightsGranter = self._createRightsGranter(cursor, uid, mix_id, context)
        log = rightsGranter.recomputeRights(isodate(first_date), isodate(last_date))

        logger.notifyChannel('gkwh_rightsgranter COMPUTE', netsvc.LOG_INFO,
                'Compute available rights')
        return log


GenerationkWhRightsGranter()


