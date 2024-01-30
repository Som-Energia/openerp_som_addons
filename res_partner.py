# -*- coding: utf-8 -*-

from osv import osv, fields
from datetime import datetime, date
from time import mktime
from dateutil.relativedelta import relativedelta
from tools.translate import _
from mongodb_backend.mongodb2 import mdbpool

from generationkwh.sharescurve import MemberSharesCurve
from generationkwh.rightspershare import RightsPerShare
from generationkwh.memberrightscurve import MemberRightsCurve
from generationkwh.memberrightsusage import MemberRightsUsage
from generationkwh.usagetracker import UsageTracker
from .remainder import RemainderProvider
from .investment import InvestmentProvider
import generationkwh.investmentmodel as gkwh


class ResPartner(osv.osv):

    _name = 'res.partner'
    _inherit = 'res.partner'

    def www_generationkwh_investments(self, cursor, uid, id, context=None):
        """
        Returns the list of investments type Generationkwh
        """
        Investment =self.pool.get('generationkwh.investment')
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: # Not a member
            return []
        return Investment.list(cursor, uid, idmap[id], 'genkwh', context=context)

    def www_aportacions_investments(self, cursor, uid, id, context=None):
        """
        Returns the list of investments type Aportacions
        """
        Investment =self.pool.get('generationkwh.investment')
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: # Not a member
            return []
        return Investment.list(cursor, uid, idmap[id], 'apo', context=context)

    def www_generationkwh_assignments(self, cursor, uid, id, context=None):
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: return [] # Not a member

        Assignments =self.pool.get('generationkwh.assignment')
        assignment_ids = Assignments.search(cursor, uid, [
            ('member_id', '=', idmap[id]),
            ('end_date', '=', False),
            ])
        def process(x):
            x['contract_name'] = x['contract_id'][1]
            x['contract_id'] = x['contract_id'][0]
            x['member_name'] = x['member_id'][1]
            x['member_id'] = x['member_id'][0]
            x['annual_use_kwh'] = x.pop('cups_anual_use')
            x['contract_address'] = x.pop('cups_direction')
            x['contract_tariff'] = x['contract_tariff'][1]
            del x['end_date']
            return x

        return sorted([
            process(x)
            for x in Assignments.read(cursor, uid, assignment_ids, [])
        ], key=lambda x: (x['priority'],x['id']))


    def www_set_generationkwh_assignment_order(self, cursor, uid, id, sorted_assignment_ids, context=None):
        Dealer = self.pool.get('generationkwh.dealer')
        Assignments = self.pool.get('generationkwh.assignment')

        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: return [] # Not a member

        # Check if all assignments are owner by the partner
        assignments = Assignments.read(cursor, uid, sorted_assignment_ids, [])
        for partner in Dealer.get_partners_by_members(
                cursor, uid, [assignment["member_id"][0] for assignment in assignments]):
            if partner[1] != id:
                raise Exception("There are different member_ids")

        # Check that all assignments are ordered at once
        actual_assignment_ids = Assignments.search(cursor, uid, [
            ('member_id', '=', idmap[id]),
            ('end_date', '=', False),
        ])
        if (
            len(actual_assignment_ids) != len(sorted_assignment_ids)
            or set(actual_assignment_ids) != set(sorted_assignment_ids)
        ):
            raise Exception("You need to order all the assignments at once")

        for order, assignment_id in enumerate(sorted_assignment_ids):
            Assignments.write(cursor, uid, [assignment_id], {'priority': order})

        return self.www_generationkwh_assignments(cursor, uid, id, context)


    def www_hourly_remaining_generationkwh(self, cursor, uid, partner_id, context=None):
        Dealer = self.pool.get('generationkwh.dealer')

        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [partner_id]))
        if not idmap: return [] # Not a member
        member_id = idmap[partner_id]

        last_invoiced_date = self._last_invoiced_date_from_priority_polissa(cursor, uid, member_id)
        start_date = last_invoiced_date - relativedelta(years=1)
        end_date = date.today()

        rightsUsage = MemberRightsUsage(mdbpool.get_db())

        rights = self._hourly_rights_generationkwh(cursor, uid, partner_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), context)
        usage = UsageTracker.convert_usage_date_quantity(enumerate(rightsUsage.usage(member_id, start_date, end_date)), start_date)

        remaining = {}
        for k,v in rights.items():
            remaining[k] = v - usage.get(k,0)

        return self._prepare_datetime_value_www_response(remaining)

    def www_hourly_rights_generationkwh(self, cursor, uid, partner_id, start_date=None, end_date=None, context=None):
        rights = self._hourly_rights_generationkwh(cursor, uid, partner_id, start_date, end_date, context)
        return self._prepare_datetime_value_www_response(rights)

    def _hourly_rights_generationkwh(self, cursor, uid, partner_id, start_date=None, end_date=None, context=None):
        if not start_date:
            start_date = gkwh.startDateRights
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        Dealer = self.pool.get('generationkwh.dealer')

        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [partner_id]))
        if not idmap: return [] # Not a member
        member_id = idmap[partner_id]

        rightsPerShare = RightsPerShare(mdbpool.get_db())
        investment = InvestmentProvider(self, cursor, uid, context)
        memberActiveShares = MemberSharesCurve(investment)
        remainders = RemainderProvider(self, cursor, uid, context)
        generatedRights = MemberRightsCurve(
            activeShares=memberActiveShares,
            rightsPerShare=rightsPerShare,
            remainders=remainders,
            eager=True,
        )

        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        rights = generatedRights.rights_kwh(member_id, start_date_dt, end_date_dt)

        return UsageTracker.convert_usage_date_quantity(enumerate((rights)), start_date_dt)

    @staticmethod
    def _prepare_datetime_value_www_response(dict_with_data):
        return [
            {
                'date': int(
                    mktime(datetime.strptime(k, '%Y-%m-%d %H:%M:%S').timetuple())
                )*1000,  # javascript works with 3 more 0 than python
                'value': dict_with_data[k]
            } for k in sorted(dict_with_data)
        ]

    def last_invoiced_date_from_priority_polissa(self, cursor, uid, member_id, context=None):
        return self._last_invoiced_date_from_priority_polissa(cursor, uid, member_id, context).strftime("%Y-%m-%d")

    def _last_invoiced_date_from_priority_polissa(self, cursor, uid, member_id, context=None):
        Polissa = self.pool.get('giscedata.polissa')
        Assignments = self.pool.get('generationkwh.assignment')
        last_invoiced_date = date.today()
        assignment_id = Assignments.search(cursor, uid, [('member_id', '=', member_id), ('priority','=', '0')])
        if assignment_id:
            priority_pol_id = Assignments.read(cursor, uid, assignment_id[0], ['contract_id'])['contract_id'][0]
            pol = Polissa.browse(cursor, uid, priority_pol_id)
            if pol.data_ultima_lectura:
                last_invoiced_date = datetime.strptime(pol.data_ultima_lectura, "%Y-%m-%d").date()
        return last_invoiced_date


ResPartner()

# vim: et sw=4 ts=4
