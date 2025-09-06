# -*- encoding: utf-8 -*-

from __future__ import print_function
from osv import osv
from tools import isolation


class act_window(osv.osv):
    _name = "ir.actions.act_window"
    _inherit = "ir.actions.act_window"

    @isolation(readonly=True, isolation_level='repeatable_read')
    def read(self, cursor, uid, ids, fields=None, context=None,
             load='_classic_read'):
        # if fields is None:
        #     self.pool.get('som.action.menu.logger').create(cursor, uid, {
        #         'act_window_id': ids[0],
        #     })

        return super(act_window, self).read(
            cursor, uid, ids, fields=fields, context=context, load=load
        )


act_window()
