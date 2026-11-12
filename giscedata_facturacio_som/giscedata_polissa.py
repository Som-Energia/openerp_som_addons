# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataPolissa(osv.osv):

    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def onchange_bloquejat(self, cursor, uid, ids, cobrament_bloquejat, context=None):
        if not cobrament_bloquejat:
            return {
                'value': {'cobrament_bloquejat': False, 'estat_pendent_cobrament': False}
            }
        return {'value': {}}

    _columns = {
        'cobrament_bloquejat': fields.boolean(
            string=u"Facturació amb cobrament bloquejat"),
        'observacions_cobrament': fields.char(
            string=u"Observacions f. cobrament bloquejat", size=170),
        'estat_pendent_cobrament': fields.many2one(
            'account.invoice.pending.state',
            string=u"Estat pendent f. cobrament bloquejat"
        )
    }

    _defaults = {
        'cobrament_bloquejat': lambda *a: False
    }


GiscedataPolissa()
