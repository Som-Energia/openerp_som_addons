# -*- coding: utf-8 -*-
from osv import osv, fields
from tools import cache


class SomSortidaState(osv.osv):
    _name = "som.sortida.state"
    _inherit = "account.invoice.pending.state"
    _description = "Estats d'una pòlissa en el procés de sortida"

    _columns = {
        'b2_02_create': fields.boolean(
            'B2-02 Create', help='Indica si aquest estat és per crear una sortida B2-02'),
    }

    _defaults = {
        'b2_02_create': False,
    }

    @cache(30)
    def get_next(self, cursor, uid, weight, process_id, context=None):
        if context is None:
            context = {}
        limit = 2
        if context.get('current_state_deactivated', False):
            limit = 1
        pstate_id = self.search(
            cursor, uid, [
                ('weight', '>=', weight),
                ('process_id', '=', process_id)
            ], limit=limit, order='weight asc', context=context)
        return pstate_id[-1]


SomSortidaState()
