# -*- coding: utf-8 -*-

from osv import osv


class GiscedataPolissa(osv.osv):

    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def write(self, cursor, user, ids, vals, context=None):
        if 'facturacio_suspesa' in vals and not vals['facturacio_suspesa']:
            vals.update({'observacio_suspesa': False})

        return super(GiscedataPolissa, self).write(cursor, user, ids, vals, context)


GiscedataPolissa()
