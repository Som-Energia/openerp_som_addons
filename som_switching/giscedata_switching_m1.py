# -*- coding: utf-8 -*-
from osv import osv


class GiscedataSwitchingM1_01(osv.osv):

    _name = "giscedata.switching.m1.01"
    _inherit = "giscedata.switching.m1.01"

    def config_step(self, cursor, uid, ids, vals, context=None):
        new_contract_values = vals.get("new_contract_values")
        if new_contract_values:
            new_contract_values.update(
                {
                    "category_id": [(6, 0, [])],
                }
            )

        super(GiscedataSwitchingM1_01, self).config_step(cursor, uid, ids, vals, context)


GiscedataSwitchingM1_01()
