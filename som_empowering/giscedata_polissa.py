import uuid
from osv import osv, fields

class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def write(self, cursor, uid, ids, vals, context=None):
        """Assign new token if partner not have
        """
        res = super(GiscedataPolissa, self).write(cursor, uid, ids, vals, context)

        partner_obj = self.pool.get('res.partner')
        if 'titular' in vals:
            partner_obj.assign_token(cursor, uid, [vals['titular']], context)
        if 'administradora' in vals:
            partner_obj.assign_token(cursor, uid, [vals['administradora']], context)

        return res

GiscedataPolissa()
# vim: et ts=4 sw=4