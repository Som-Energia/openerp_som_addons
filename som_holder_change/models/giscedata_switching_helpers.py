# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class GiscedataSwitchingHelpers(osv.osv):
    _name = "giscedata.switching.helpers"
    _inherit = "giscedata.switching.helpers"

    def activar_polissa_from_m1_canvi_titular(self, cursor, uid, sw_id, context=None):
        result = super(GiscedataSwitchingHelpers, self).activar_polissa_from_m1_canvi_titular(
            cursor, uid, sw_id, context=context
        )
        if result[0] == "OK":
            self.pool.get("som.holder.change.request")._apply_subrogation_card_payment(
                cursor, uid, sw_id, context=context
            )
        return result


GiscedataSwitchingHelpers()
