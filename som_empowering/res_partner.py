import uuid

from osv import osv, fields
from mongodb_backend.mongodb2 import mdbpool


def generate_token():
    return ''.join([uuid.uuid4().hex for _ in range(0, 2)])


class ResPartner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def assign_token(self, cursor, uid, ids, context=None):
        """Assign a new token to the partner
        """
        polissa_obj = self.pool.get('giscedata.polissa')
        m = mdbpool.get_db()
        for partner in self.read(cursor, uid, ids, ['empowering_token']):
            m.tokens.remove({'token': partner['empowering_token']})
            token = generate_token()
            self.write(cursor, uid, [partner['id']], {
                'empowering_token': token
            })
            allowed = polissa_obj.search(cursor, uid, [
                '|',
                    ('titular.id', '=', partner['id']),
                    ('administradora.id', '=', partner['id'])
            ])
            if allowed:
                allowed = [{'name': x.name, 'cups': x.cups.name}
                           for x in polissa_obj.browse(cursor, uid, allowed)]
                m.tokens.insert({
                    'token': token,
                    'allowed_contracts': allowed
                })
        return True

    _columns = {
        'empowering_token': fields.char('Empowering token', readonly=True, size=256)
    }

ResPartner()
