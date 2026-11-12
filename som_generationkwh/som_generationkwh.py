# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields
import netsvc
from mongodb_backend.mongodb2 import mdbpool
from tools import config

from generationkwh.dealer import Dealer
from generationkwh.sharescurve import MemberSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.rightscorrection import RightsCorrection
from generationkwh.memberrightscurve import MemberRightsCurve
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.fareperiodcurve import FarePeriodCurve
from generationkwh.usagetracker import UsageTracker
from generationkwh.isodates import isodate
from .emission import GenerationkwhEmission
from .assignment import AssignmentProvider
from .remainder import RemainderProvider
from .investment import InvestmentProvider
from .holidays import HolidaysProvider
import datetime

# Models


class GenerationkWhDealer(osv.osv):

    _name = 'generationkwh.dealer'
    _auto = False

    def is_active(self, cursor, uid,
                  contract_id, first_date, last_date,
                  context=None):
        """ Returns True if contract_id has generation kwh activated
            during the period"""
        dealer = self._createDealer(cursor, uid, context)

        if type(first_date) != datetime.date:
            first_date = isodate(first_date)

        if type(last_date) != datetime.date:
            last_date = isodate(last_date)

        return dealer.is_active(
            contract_id, first_date, last_date)

    def _get_available_kwh(self, cursor, uid,
                          contract_id, first_date, last_date, fare_id, period_id,
                          context=None):
        """ Returns generationkwh [kWh] available for contract_id during the
            date interval, fare and period"""
        dealer = self._createDealer(cursor, uid, context)

        fare, period = self.get_fare_name_by_id(cursor, uid, fare_id, period_id)

        return dealer.get_available_kwh(
            contract_id, first_date, last_date, fare, period)

    def get_members_by_partners(self, cursor, uid, partner_ids, context=None):
        Soci = self.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [('partner_id','in',partner_ids)], context=context)
        res = Soci.read(cursor, uid, member_ids, ['partner_id'], context=context)
        return [ (r['partner_id'][0], r['id'])
            for r in res
            ]

    def get_members_by_codes(self, cursor, uid, codes, context=None):
        completedCodes = [
            "S"+str(code).zfill(6)
            for code in codes
            ]
        Soci = self.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [('ref','in',completedCodes)], context=context)
        res = Soci.read(cursor, uid, member_ids, ['ref'], context=context)
        return [ (r['ref'], r['id'])
            for r in res
            ]

    def get_members_by_vats(self, cursor, uid, vats, context=None):
        # TODO: Prepend ES just when detected as NIF
        vats = ['ES'+vat for vat in vats]
        Soci = self.pool.get('somenergia.soci')
        member_ids = Soci.search(cursor, uid, [('vat','in',vats)], context=context)
        res = Soci.read(cursor, uid, member_ids, ['vat'], context=context)
        return [ (r['vat'][0], r['id'])
            for r in res
            ]

    def get_partners_by_members(self, cursor, uid, member_ids, context=None):
        Soci = self.pool.get('somenergia.soci')
        res = Soci.read(cursor, uid, member_ids, ['partner_id'], context=context)
        return [
            (r['id'], r['partner_id'][0])
            for r in res
            ]

    def get_contracts_by_ref(self, cursor, uid, contract_refs, context=None):
        contract_refs = map(str, contract_refs)
        Contract = self.pool.get('giscedata.polissa')
        contract_ids = Contract.search(cursor, uid, [
            ('name', 'in', contract_refs),
            ], context=context)
        res = Contract.read(cursor, uid, contract_ids, ['name'], context=context)
        return [ (r['name'], r['id'])
            for r in res
            ]

    def get_fare_name_by_id(self, cursor, uid, fare_id, period_id, context=None):
        Fare = self.pool.get('giscedata.polissa.tarifa')
        Period = self.pool.get('giscedata.polissa.tarifa.periodes')

        return (
            Fare.read(cursor, uid, fare_id, ['name'])['name'],
            Period.read(cursor, uid, period_id, ['name'])['name']
        )

    def use_kwh(self, cursor, uid,
                contract_id, first_date, last_date, fare_id, period_id, kwh,
                context=None):
        """Marks the indicated kwh as used, if available, for the contract,
           date interval, fare and period and returns the ones efectively used.
        """

        logger = netsvc.Logger()

        dealer = self._createDealer(cursor, uid, context)

        fare, period = self.get_fare_name_by_id(cursor, uid, fare_id, period_id)

        res = dealer.use_kwh(
            contract_id, isodate(first_date), isodate(last_date), fare, period, kwh)

        socis = [ line['member_id'] for line in res ]
        members2partners = dict(self.get_partners_by_members(cursor, uid, socis, context=context))

        def soci2partner(soci):
            return members2partners[soci]

        for line in res:
            txt = (u'{kwh} Generation kwh of member {member} to {contract} '
                   u'for period {period} between {start} and {end}').format(
                    kwh=line['kwh'],
                    member=line['member_id'],
                    contract=contract_id,
                    period=period,
                    start=first_date,
                    end=last_date,
            )
            logger.notifyChannel('gkwh_dealer USE', netsvc.LOG_INFO, txt)

        return [
            dict(
                member_id = soci2partner(line['member_id']),
                kwh = line['kwh'],
                usage=line['usage']
                )
            for line in res
        ]


    def refund_kwh(self, cursor, uid,
                   contract_id, first_date, last_date, fare_id, period_id, kwh,
                   partner_id, context=None):
        """Refunds the indicated kwh, marking them as available again, for the
           contract, date interval, fare and period and returns the ones
           efectively used.
        """
        logger = netsvc.Logger()

        fare, period = self.get_fare_name_by_id(cursor, uid, fare_id, period_id)

        partner2member = dict(self.get_members_by_partners(cursor, uid, [partner_id], context=context))
        try:
            member_id = partner2member[partner_id]
        except KeyError:
            return 0

        txt = (u'{kwh} Generation kwh of member {member} to {contract} '
               u'for period {period} between {start} and {end}').format(
             contract=contract_id,
             period=period,
             start=first_date,
             end=last_date,
             member=member_id,
             kwh=kwh
        )
        logger.notifyChannel('gkwh_dealer REFUND', netsvc.LOG_INFO, txt)

        dealer = self._createDealer(cursor, uid, context)
        res = dealer.refund_kwh(
            contract_id,
            isodate(first_date),
            isodate(last_date),
            fare, period, kwh, member_id)
        return res

    def _createTracker(self, cursor, uid, context):

        investments = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investments)
        rightsPerShare = RightsPerShare(mdbpool.get_db())
        remainders = RemainderProvider(self, cursor, uid, context)

        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            remainders=remainders,
            eager=True,
            )

        rightsUsage = MemberRightsUsage(mdbpool.get_db())

        holidays = HolidaysProvider(self, cursor, uid, context)
        farePeriod = FarePeriodCurve(holidays)

        return UsageTracker(generatedRights, rightsUsage, farePeriod)

    def _createDealer(self, cursor, uid, context):

        investments = InvestmentProvider(self, cursor, uid, context)
        usageTracker = self._createTracker(cursor, uid, context)
        assignments = AssignmentProvider(self, cursor, uid, context)
        return Dealer(usageTracker, assignments, investments)

GenerationkWhDealer()


class GenerationkWhTestHelper(osv.osv):
    """
        Helper model that enables accessing data providers
        from tests written with erppeek.
    """

    _name = 'generationkwh.testhelper'
    _auto = False

    def holidays(self, cursor, uid,
            start, stop,
            context=None):
        holidaysProvider = HolidaysProvider(self, cursor, uid, context)
        return holidaysProvider.get(start, stop)

    def memberrightsusage_update(self, cursor, uid,
            member,start,data,
            context=None):
        usage_provider = MemberRightsUsage(mdbpool.get_db())
        usage_provider.updateUsage(
            member=member,
            start=isodate(start),
            data=data
            )

    def setup_rights_per_share(self, cursor, uid,
            nshares, firstDate, data,
            context=None):
        rightsPerShare = RightsPerShare(mdbpool.get_db())
        rightsPerShare.updateRightsPerShare(nshares, isodate(firstDate), data)
        remainders = RemainderProvider(self, cursor, uid, context)
        lastDate = isodate(firstDate) + datetime.timedelta(days=(len(data)+24)//25)
        remainders.updateRemainders([
            (nshares, isodate(firstDate), 0),
            (nshares, lastDate, 0),
            ])

    def rights_per_share(self, cursor, uid,
            nshares, firstDate, lastDate,
            context=None):
        rights = RightsPerShare(mdbpool.get_db())
        return list(int(i) for i in rights.rightsPerShare(nshares,
                isodate(firstDate),
                isodate(lastDate)
                ))

    def rights_correction(self, cursor, uid,
            nshares, firstDate, lastDate,
            context=None):
        correction = RightsCorrection(mdbpool.get_db())
        return list(int(i) for i in correction.rightsCorrection(nshares,
                isodate(firstDate),
                isodate(lastDate)
                ))

    def clear_mongo_collections(self, cursor, uid, collections, context=None):

        Config = self.pool.get('res.config')
        destructiveAllowed = Config.get('destructive_testing_allowed', False)
        if not destructiveAllowed:
            raise Exception("Trying to drop Mongo collections in production!")

        for collection in collections:
            mdbpool.get_db().drop_collection(collection)

    def rights_kwh(self, cursor, uid, member, start, stop, context=None):
        investment = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investment)
        rightsPerShare = RightsPerShare(mdbpool.get_db())
        remainders = RemainderProvider(self, cursor, uid, context)
        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            remainders=remainders,
            eager=True,
            )
        return [ int(num) for num in generatedRights.rights_kwh(member,
            isodate(start),
            isodate(stop),
            )]

    def member_shares(self, cursor, uid, member, start, stop, context=None):
        investment = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investment)
        return [ int(num) for num in memberActiveShares.hourly(
            isodate(start),
            isodate(stop),
            member,
            )]
        


    def trace_rigths_compilation(self, cursor, uid,
            member, start, stop, fare, period,
            context=None):
        """
            Helper function to show data related to computation of available
            rights.
        """
        print "Dropping results for", member, start, stop, fare, period

        investment = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investment)
        rightsPerShare = RightsPerShare(mdbpool.get_db())
        remainders = RemainderProvider(self, cursor, uid, context)

        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            remainders=remainders,
            eager=True,
            )
        rightsUsage = MemberRightsUsage(mdbpool.get_db())
        holidays = HolidaysProvider(self, cursor, uid, context)
        farePeriod = FarePeriodCurve(holidays)

        print 'remainders', remainders.lastRemainders()
        print 'investment', investment.items(
            start=isodate(start),
            end=isodate(stop),
            member=member)
        print 'active', memberActiveShares.hourly(
            isodate(start),
            isodate(stop),
            member)
        for nshares in set(memberActiveShares.hourly(
            isodate(start),
            isodate(stop),
            member)):
            print 'rightsPerShare', nshares, rightsPerShare.rightsPerShare(nshares,
                isodate(start),
                isodate(stop),
                )
        print 'rights', generatedRights.rights_kwh(member,
            isodate(start),
            isodate(stop),
            )

        print 'periodmask', farePeriod.periodMask(
            fare, period,
            isodate(start),
            isodate(stop),
            )

    def usage(self, cursor, uid,
            member_id, first_date, last_date,
            context=None):
        rightsUsage = MemberRightsUsage(mdbpool.get_db())
        result = list(int(i) for i in rightsUsage.usage(
            member_id,
            isodate(first_date),
            isodate(last_date)
            ))
        return result

    def usagetracker_available_kwh(self, cursor, uid,
            member, start, stop, fare, period,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        usageTracker = GenerationkWhDealer._createTracker(cursor, uid, context)
        result = usageTracker.available_kwh(
            member,
            isodate(start),
            isodate(stop),
            fare,
            period
            )
        return result

    def usagetracker_use_kwh(self, cursor, uid,
            member, start, stop, fare, period, kwh,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        usageTracker = GenerationkWhDealer._createTracker(cursor, uid, context)
        result = usageTracker.use_kwh(
            member,
            isodate(start),
            isodate(stop),
            fare,
            period,
            kwh,
            )
        return int(result)

    def usagetracker_refund_kwh(self, cursor, uid,
            member, start, stop, fare, period, kwh,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        usageTracker = GenerationkWhDealer._createTracker(cursor, uid, context)
        result = usageTracker.refund_kwh(
            member,
            isodate(start),
            isodate(stop),
            fare,
            period,
            kwh,
            )
        return int(result)

    def dealer_use_kwh(self, cursor, uid,
            contract, start, stop, fare, period, kwh,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        dealer = GenerationkWhDealer._createDealer(cursor, uid, context)
        result = dealer.use_kwh(
            contract,
            isodate(start),
            isodate(stop),
            fare,
            period,
            kwh,
            )
        return result

    def dealer_refund_kwh(self, cursor, uid,
            contract_id, start, stop, fare, period, kwh, member,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        dealer = GenerationkWhDealer._createDealer(cursor, uid, context)
        result = dealer.refund_kwh(
            contract_id,
            isodate(start),
            isodate(stop),
            fare,
            period,
            kwh,
            member,
            )
        return int(result)

    def dealer_is_active(self, cursor, uid,
            contract_id, start, stop,
            context=None):

        GenerationkWhDealer = self.pool.get('generationkwh.dealer')
        dealer = GenerationkWhDealer._createDealer(cursor, uid, context)
        result = dealer.is_active(
            contract_id,
            isodate(start),
            isodate(stop),
            )
        return result


GenerationkWhTestHelper()




class GenerationkWhInvoiceLineOwner(osv.osv):
    """ Class with the relation between generation invoice line and rights owner
    """

    _name = 'generationkwh.invoice.line.owner'

    def name_get(self, cursor, uid, ids, context=None):
        """GkWH name"""
        res = []
        glo_vals = self.read(cursor, uid, ids, ['factura_line_id'])
        for glo in glo_vals:
            res.append((glo['id'], glo['factura_line_id'][1]))

        return res

    def _ff_invoice_number(self, cursor, uid, ids, field_name, arg,
                           context=None ):
        """Invoice Number"""
        if not ids:
            return []
        res = dict([(i, False) for i in ids])
        f_obj = self.pool.get('giscedata.facturacio.factura')

        glo_vals = self.read(cursor, uid, ids, ['factura_id'])
        inv_ids = [g['factura_id'][0] for g in glo_vals]
        inv_vals = f_obj.read(cursor, uid, inv_ids, ['number'])
        inv_dict = dict([(i['id'], i['number']) for i in inv_vals])
        for glo_val in glo_vals:
            glo_id = glo_val['id']
            glo_number = inv_dict[glo_val['factura_id'][0]]
            res.update({glo_id: glo_number})

        return res

    def getPriceWithoutGeneration(self, cr, uid, line):
        per_obj = self.pool.get('giscedata.polissa.tarifa.periodes')
        gff_obj = self.pool.get('giscedata.facturacio.factura')
        gffl_obj = self.pool.get('giscedata.facturacio.factura.linia')

        fare_period = gff_obj.get_fare_period(cr, uid, line['product_id'])
        product_id_nogen = per_obj.read(cr, uid, fare_period, ['product_id'])['product_id'][0]
        line_s_gen_id = gffl_obj.search(cr, uid, [
            ('invoice_id','=', line['invoice_id'][0]),('product_id','=',product_id_nogen),
            ('data_desde', '=', line['data_desde']),
        ])
        line_s_gen = gffl_obj.read(cr, uid, line_s_gen_id[0])
        return line_s_gen

    def getProfit(self, cr, uid, line):
        ai_obj = self.pool.get('account.invoice')
        cfg_obj = self.pool.get('res.config')
        gffl_obj = self.pool.get('giscedata.facturacio.factura.linia')

        if line['quantity'] == 0:
            return 0

        start_date_mecanisme_ajust_gas = cfg_obj.get(
            cr, uid, 'start_date_mecanisme_ajust_gas', '2022-10-01')
        end_date_mecanisme_ajust_gas = cfg_obj.get(
            cr, uid, 'end_date_mecanisme_ajust_gas', '2099-12-31')

        priceNoGen = float(self.getPriceWithoutGeneration(cr, uid, line)['price_unit'])
        rmag_lines = gffl_obj.browse(cr, uid, line['id']).factura_id.get_rmag_lines()
        if rmag_lines and \
                line['data_desde'] >= start_date_mecanisme_ajust_gas and \
                line['data_fins'] <= end_date_mecanisme_ajust_gas:
            rmag_line = gffl_obj.browse(cr, uid, rmag_lines[0])
            profit = (priceNoGen + rmag_line.price_unit - line['price_unit']) * line['quantity']
        else:
            profit = (priceNoGen - line['price_unit']) * line['quantity']

        if ai_obj.read(cr, uid, line['invoice_id'][0], ['type'])['type'] == 'out_refund':
            return round(profit * -1, 2)
        return round(profit ,2)


    def _ff_saving_generation(self, cursor, uid, ids, field_name, arg,
                           context=None ):
        """Invoice Number"""
        if not ids:
            return []
        gilo_obj = self.pool.get('generationkwh.invoice.line.owner')
        gffl_obj = self.pool.get('giscedata.facturacio.factura.linia')

        res = {k: {} for k in ids}

        for gilo_line in self.browse(cursor, uid, ids):
            line = gffl_obj.read(cursor, uid, gilo_line.factura_line_id.id)
            res[gilo_line.id] = self.getProfit(cursor, uid, line)

        return res

    _columns = {
        'factura_id': fields.many2one(
            'giscedata.facturacio.factura', 'Factura', required=True,
            readonly=True
        ),
        'factura_number': fields.function(
            _ff_invoice_number, string='Num. Factura', method=True, type='char',
            size='64',
        ),
        'factura_line_id': fields.many2one(
            'giscedata.facturacio.factura.linia', 'Línia de factura',
            required=True, readonly=True
        ),
        'owner_id': fields.many2one(
            'res.partner', 'Soci Generation', required=True, readonly=True
        ),
        'saving_gkw_amount': fields.function(
            _ff_saving_generation, string='Estalvi Generation',
            method=True, type='float',
            digits=(16, int(config['price_accuracy'])), store=True,
        ),
        'right_usage_lines': fields.one2many(
            'generationkwh.right.usage.line', 'line_owner',
            'Drets emprats', readonly=True, ondelete='cascade'
        )
    }

GenerationkWhInvoiceLineOwner()


class GenerationkWhRightUsageLine(osv.osv):
    """ Class with the relation between generation invoice line and rights owner
    """

    _name = 'generationkwh.right.usage.line'
    _order = 'datetime'

    _columns = {
        'datetime': fields.datetime(
            'Data generació drets',required=True, readonly=True
        ),
        'quantity': fields.integer(
            'KWh utilitzats', required=True, readonly=True
        ),
        'line_owner': fields.many2one(
            'generationkwh.invoice.line.owner', 'Propietari drets GkWh factura',
            required=True, readonly=True, ondelete='cascade'
        ),
        'owner_id' : fields.related(
            'line_owner', 'owner_id', type='many2one', relation='res.partner',
            string="Propietari", readonly=True
        ),
        'factura_id' : fields.related(
            'line_owner', 'factura_id', type='many2one',
            relation='giscedata.facturacio.factura', string="Factura", readonly=True
        ),
    }

GenerationkWhRightUsageLine()

# vim: ts=4 sw=4 et
