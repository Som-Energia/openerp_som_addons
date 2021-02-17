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
            partner_token = partner_obj.read(cursor, uid, vals['titular'], ['empowering_token'])
            if not partner_token['empowering_token']:
                partner_obj.assign_token(cursor, uid, [vals['titular']], context)

        if 'pagador' in vals:
            partner_token = partner_obj.read(cursor, uid, vals['pagador'], ['empowering_token'])
            if not partner_token['empowering_token']:
                partner_obj.assign_token(cursor, uid, [vals['pagador']], context)

        if 'notificador' in vals:
            partner_token = partner_obj.read(cursor, uid, vals['notificador'], ['empowering_token'])
            if not partner_token['empowering_token']:
                partner_obj.assign_token(cursor, uid, [vals['notificador']], context)

        return res

GiscedataPolissa()
# vim: et ts=4 sw=4
