# -*- coding: utf-8 -*-

from osv import osv, fields

class ResPartner(osv.osv):

    _name = 'res.partner'
    _inherit = 'res.partner'

    def www_generationkwh_investments(self, cursor, uid, id, context=None):
        """
        Returns the list of investments
        """
        Investment =self.pool.get('generationkwh.investment')
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: # Not a member
            return []
        return Investment.list(cursor, uid, idmap[id], context=context)

    def www_generationkwh_assignments(self, cursor, uid, id, context=None):
        Dealer =self.pool.get('generationkwh.dealer')
        idmap = dict(Dealer.get_members_by_partners(cursor, uid, [id]))
        if not idmap: return [] # Not a member

        Assignments =self.pool.get('generationkwh.assignment')
        assignment_ids = Assignments.search(cursor, uid, [
            ('member_id', '=', idmap[id]),
            ])
        def process(x):
            x['contract_name'] = x['contract_id'][1]
            x['contract_id'] = x['contract_id'][0]
            x['member_name'] = x['member_id'][1]
            x['member_id'] = x['member_id'][0]
            x['annual_use_kwh'] = x.pop('cups_anual_use')
            return x

        return sorted([
            process(x)
            for x in Assignments.read(cursor, uid, assignment_ids, [])
        ], key=lambda x: (x['priority'],x['id']))




ResPartner()

# vim: et sw=4 ts=4
