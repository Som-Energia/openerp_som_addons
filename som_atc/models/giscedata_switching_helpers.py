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

    def create_crm_case_titular_autoconsum(self, cursor, uid, partner_vals, step):
        atc_ids = super(GiscedataSwitchingHelpers, self).create_crm_case_titular_autoconsum(
            cursor, uid, partner_vals, step
        )

        self._auto_call_wizard_change_state_atr(cursor, uid, atc_ids, 'open')
        self._auto_call_wizard_change_state_atr(cursor, uid, atc_ids, 'close')

    def _auto_call_wizard_change_state_atr(self, cursor, uid, atc_ids, new_state):
        wiz_obj = self.pool.get('wizard.change.state.atc')
        wiz_id = wiz_obj.create(cursor, uid, {'new_state': 'open'})
        try:
            wiz_obj.perform_change(cursor, uid, [wiz_id], context={'active_ids': atc_ids})
        except Exception:
            raise osv.except_osv('Error', 'Error en ATC multi canvi a ' + new_state)


GiscedataSwitchingHelpers()
