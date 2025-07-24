# -*- coding: utf-8 -*-
from osv import osv, fields


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


SomSortidaState()
