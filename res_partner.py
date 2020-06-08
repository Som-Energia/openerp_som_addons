# -*- coding: utf-8 -*-

from osv import osv, fields
from datetime import datetime, date
from tools.translate import _


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
            del x['end_date']
            return x

        return sorted([
            process(x)
            for x in Assignments.read(cursor, uid, assignment_ids, [])
        ], key=lambda x: (x['priority'],x['id']))

        def delete_rel(cursor, uid, categ_id, res_partner_id):
            cursor.execute('delete from res_partner_category_rel where category_id=%s and partner_id=%s',(categ_id, res_partner_id))
        
        res_users = self.pool.get('res.users')
        usuari = res_users.read(cursor, uid, uid, ['name'])['name']
        old_comment = soci_obj.read(cursor, uid, [member_id], ['comment'])[0]['comment']
        old_comment = old_comment + '\n' if old_comment else '' 
        comment =  "{}Baixa efectuada a data {} per: {}".format(old_comment, today, usuari)
        soci_obj.write(cursor, uid, [member_id], {'baixa': True,
                                                'data_baixa_soci': today,
                                                'comment': comment })
        delete_rel(cursor, uid, soci_category_id, res_partner_id)




ResPartner()

# vim: et sw=4 ts=4
