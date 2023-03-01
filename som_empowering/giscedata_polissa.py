import uuid
from osv import osv, fields

class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def _modified_partners(self, cursor, uid, ids, vals):
        """
        Given some fields to be changed in a set of contracts,
        it returns the partners that will need to update their token.
        """
        if 'pagador' in vals:
            polissa = self.read(cursor, uid, ids, ['pagador'])
            return [polissa['pagador'][0]]
        if 'titular' in vals:
            polissa = self.read(cursor, uid, ids, ['titular'])
            return [polissa['titular'][0]]
        return []

    def write(self, cursor, uid, ids, vals, context=None):
        """Assign new token if partner not have
        """
        res = super(GiscedataPolissa, self).write(cursor, uid, ids, vals, context)

        partner_obj = self.pool.get('res.partner')
        partners_to_update_token=set()
        if 'titular' in vals:
            partners_to_update_token.add(vals['titular'])
        if 'pagador' in vals:
            partners_to_update_token.add(vals['pagador'])

        partner_obj.assign_token(cursor, uid, list(partners_to_update_token), context)

        return res

GiscedataPolissa()
# vim: et ts=4 sw=4
