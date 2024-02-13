# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


class GiscedataSwitchingHelpers(osv.osv):

    _name = "giscedata.switching.helpers"
    _inherit = "giscedata.switching.helpers"

    def perform_cac_actions_from_sw_id(self, cursor, uid, sw_id, params, context=None):
        ret = super(GiscedataSwitchingHelpers, self).perform_cac_actions_from_sw_id(
            cursor, uid, sw_id, params, context=context
        )

        try:
            sw_obj = self.pool.get("giscedata.switching")
            atc_o = self.pool.get("giscedata.atc")

            cac_id = None
            sw = sw_obj.browse(cursor, uid, sw_id)
            if sw.ref and sw.ref.split(",")[0] == "giscedata.atc":
                cac_id = int(sw.ref.split(",")[1])
            elif sw.ref and sw.ref.split(",")[0] == "giscedata.atc":
                cac_id = int(sw.ref.split(",")[1])

            if cac_id:  # triggers the update of the process_step stored field function
                vals = atc_o.read(cursor, uid, cac_id, ["ref", "ref2"], context=context)
                vals.pop("id")
                atc_o.write(cursor, uid, cac_id, vals, context=context)

        except Exception as e:
            raise Exception(e.message, _(u"ERROR"))

        return ret


GiscedataSwitchingHelpers()
