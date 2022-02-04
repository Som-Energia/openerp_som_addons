# -*- coding: utf-8 -*-

import os
from osv import osv, fields
from mongodb_backend import osv_mongodb
from mongodb_backend.mongodb2 import mdbpool
from .erpwrapper import ErpWrapper
from yamlns import namespace as ns

from datetime import datetime
from plantmeter.resource import ProductionAggregator, ProductionPlant, ProductionMeter 
from plantmeter.mongotimecurve import MongoTimeCurve, toLocal, asUtc
from somutils.isodates import isodate, naiveisodatetime, localisodate

class GenerationkwhProductionAggregator(osv.osv):
    """
    Serialization class for a plant mix. See plantmeter.aggregator.
    A mix would be a set of plants which production is to be added together.
    """

    _name = 'generationkwh.production.aggregator'


    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'plants': fields.one2many('generationkwh.production.plant', 'aggr_id', 'Plants')
    }

    _defaults = {
        'enabled': lambda *a: False
    }

    def get_kwh(self, cursor, uid, mix_id, start, end, context=None):
        '''Get production aggregation'''
   
        if not context:
            context = {}
        _aggr = self._createAggregator(cursor, uid, mix_id)
        return _aggr.get_kwh(start, end).tolist()

    def firstActiveDate(self, cursor, uid, mix_id, context=None):
        '''Get first measurement date'''

        if not context:
            context = {}
        _aggr = self._createAggregator(cursor, uid, mix_id)
        date = _aggr.firstActiveDate()
        return date if date else None

    def firstMeasurementDate(self, cursor, uid, mix_id, context=None):
        '''Get first measurement date'''

        if not context:
            context = {}
        _aggr = self._createAggregator(cursor, uid, mix_id)
        date = _aggr.firstMeasurementDate()
        return date if date else None

    def lastMeasurementDate(self, cursor, uid, mix_id, context=None):
        '''Get last measurement date'''

        if not context:
            context = {}
        _aggr = self._createAggregator(cursor, uid, mix_id)
        date = _aggr.lastMeasurementDate()
        return date if date else None

    def _createAggregator(self, cursor, uid, mix_id):
        def extract_attrs(obj, attrs):
            # extracts name value tuples from erp browse object
            return {attr: getattr(obj, attr) for attr in attrs}

        if isinstance(mix_id, list) or isinstance(mix_id, tuple):
            mix_id = mix_id[0]

        aggr = self.browse(cursor, uid, mix_id)
        curveProvider = MongoTimeCurve(mdbpool.get_db(),
            'tm_profile',
            creationField = 'create_date',
            timestampField = 'utc_gkwh_timestamp',
            )

        # TODO: Clean initialization method
        args = ['id', 'name', 'description', 'enabled']
        return ProductionAggregator(**dict(
            extract_attrs(aggr, args),
            plants=[
                ProductionPlant(**dict(
                    extract_attrs(plant, args+['first_active_date']),
                    meters=[
                        ProductionMeter(
                            curveProvider=curveProvider,
                            **extract_attrs(meter, args + ['first_active_date'])
                            )
                        for meter in plant.meters
                        if meter.enabled
                        ],
                    ))
                for plant in aggr.plants
                if plant.enabled
                ],
            ))

GenerationkwhProductionAggregator()


class GenerationkwhProductionPlant(osv.osv):
    """
    Serialization class for a plant. See plantmeter.plant.
    """

    _name = 'generationkwh.production.plant'
    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'nshares': fields.integer('Number of shares'),
        'aggr_id': fields.many2one('generationkwh.production.aggregator', 'Production aggregator',
                                  required=True),
        'meters': fields.one2many('generationkwh.production.meter', 'plant_id', 'Meters'),
        'first_active_date': fields.date('First operative date'),
        'last_active_date': fields.date('Last operative date'),
    }
    _defaults = {
        'enabled': lambda *a: False,
    }


GenerationkwhProductionPlant()


class GenerationkwhProductionMeter(osv.osv):
    """
    Serialization class for a plant meter. See plantmeter.meter.
    """

    _name = 'generationkwh.production.meter'
    _columns = {
        'name': fields.char('Name', size=50),
        'description': fields.char('Description', size=150),
        'enabled': fields.boolean('Enabled'),
        'plant_id': fields.many2one('generationkwh.production.plant'),
        'first_active_date': fields.date('First operative date'),
        }
    _defaults = {
        'enabled': lambda *a: False,
    }

GenerationkwhProductionMeter()

class PlantShareProvider(ErpWrapper):
    """
    Provides a list for each plant of their active periods and their share value.
    To be used as provider for a LayeredShareCurve, that generates
    the curves to represent the share value of the active built plants.
    """
    def __init__(self, erp, cursor, uid, mixname, context=None):
        self.mixname = mixname
        super(PlantShareProvider, self).__init__(erp, cursor, uid, context)

    def items(self):
        Mix = self.erp.pool.get('generationkwh.production.aggregator')
        Plant = self.erp.pool.get('generationkwh.production.plant')
        mix_ids = Mix.search(self.cursor, self.uid, [
            ('name', '=', self.mixname)
        ])
        # TODO: if not mixids: ....

        plant_ids = Plant.search(self.cursor, self.uid, [
            ('aggr_id', '=', mix_ids[0]),
        ])
        plants = Plant.read(self.cursor, self.uid, plant_ids, [
        ])
        return [
            ns(
                mix=self.mixname,
                shares=plant['nshares'],
                firstEffectiveDate = isodate(plant['first_active_date']),
                lastEffectiveDate = isodate(plant['last_active_date']),
            )
            for plant in plants
        ]



class GenerationkwhProductionMeasurement(osv_mongodb.osv_mongodb):

    _name = 'generationkwh.production.measurement'
    _order = 'timestamp desc'

    _columns = {
        'name': fields.integer('Plant identifier'), # NOTE: workaround due mongodb backend
        'create_at': fields.datetime('Create datetime'),
        'datetime': fields.datetime('Exported datetime'),
        'daylight': fields.char('Exported datetime daylight',size=1),
        'ae': fields.float('Exported energy (kWh)')
    }

    def search(self, cursor, uid, args, offset=0, limit=0, order=None,
               context=None, count=False):
        '''Exact match for name.
        In mongodb, even when an index exists, not exact
        searches for fields scan all documents in collection
        making it extremely slow. Making name exact search
        reduces dramatically the amount of documents scanned'''

        new_args = []
        for arg in args:
            if not isinstance(arg, (list, tuple)):
                new_args.append(arg)
                continue
            field, operator, value = arg
            if field == 'name' and operator != '=':
                operator = '='
            new_args.append((field, operator, value))
        return super(GenerationkwhProductionMeasurement,
                     self).search(cursor, uid, new_args,
                                  offset=offset, limit=limit,
                                  order=order, context=context,
                                  count=count)

GenerationkwhProductionMeasurement()



class GenerationkwhProductionAggregatorTesthelper(osv.osv):
    '''Implements generationkwh production aggregation testhelper '''

    _name = 'generationkwh.production.aggregator.testhelper'
    _auto = False


    def get_kwh(self, cursor, uid, mix_id, start, end, context=None):
        mix = self.pool.get('generationkwh.production.aggregator')
        return mix.get_kwh(cursor, uid, mix_id,
                isodate(start), isodate(end), context)

    def firstActiveDate(self, cursor, uid, mix_id, context=None):
        mix = self.pool.get('generationkwh.production.aggregator')
        result = mix.firstActiveDate(cursor, uid, mix_id, context)
        return result and str(result)

    def firstMeasurementDate(self, cursor, uid, mix_id, context=None):
        mix = self.pool.get('generationkwh.production.aggregator')
        result = mix.firstMeasurementDate(cursor, uid, mix_id, context)
        return result and str(result)

    def lastMeasurementDate(self, cursor, uid, mix_id, context=None):
        production = self.pool.get('generationkwh.production.aggregator')
        result = production.lastMeasurementDate(cursor, uid, mix_id, context)
        return result and str(result)

    def clear_mongo_collections(self, cursor, uid, collections, context=None):
        for collection in collections:
            mdbpool.get_db().drop_collection(collection)

    def fillMeasurements(self, cursor, uid, first_date, meter_name, values):
        curveProvider = MongoTimeCurve(mdbpool.get_db(),
            'tm_profile',
            creationField = 'create_date',
            timestampField = 'utc_gkwh_timestamp',
            )
        curveProvider.update(
            start = localisodate(first_date),
            filter = meter_name,
            field = 'ae',
            data = values,
            )

    def fillMeasurementPoint(self, cursor, uid, pointTime, name, value, context=None):
        curveProvider = MongoTimeCurve(mdbpool.get_db(),
            'tm_profile',
            creationField = 'create_date',
            timestampField = 'utc_gkwh_timestamp',
            )
        curveProvider.fillPoint(
            datetime=toLocal(asUtc(naiveisodatetime(pointTime))),
            name=name,
            ae=value)

    def plantShareItems(self, cursor, uid, mixname):
        provider = PlantShareProvider(self, cursor, uid, mixname, context={})
        return [
            dict(
                item,
                lastEffectiveDate=str(item.lastEffectiveDate),
                firstEffectiveDate=str(item.firstEffectiveDate),
            )
            for item in provider.items()
        ]



GenerationkwhProductionAggregatorTesthelper()


# vim: ts=4 sw=4 et
