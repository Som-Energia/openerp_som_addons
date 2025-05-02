# -*- encoding: utf-8 -*-

from __future__ import print_function
from osv import osv
from tools import isolation


class ir_values(osv.osv):
    _name = "ir.values"
    _inherit = "ir.values"

    @isolation(readonly=True, isolation_level='repeatable_read')
    def get(
        self, cr, uid, key, key2, models, meta=False, context={}, res_id_req=False,
        without_user=True, key2_req=True
    ):
        res = super(ir_values, self).get(
            cr, uid, key, key2, models, meta=meta, context=context, res_id_req=res_id_req,
            without_user=without_user, key2_req=key2_req
        )

        if key == 'default' and key2 is False and 'wiz' in models[0]:
            self.pool.get('som.action.wzrd.logger').create(cr, uid, {
                'model': models[0],
            })

        if key == 'action' and key2 == 'tree_but_open':
            self.pool.get('som.action.menu.logger').create(cr, uid, {
                'act_window_id': res[0][2]['id'],
            })

        return res


ir_values()
