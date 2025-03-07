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
        self._tmp_atc_ids = atc_ids  # Trick to temporally save the ATC_IDS
        return atc_ids

    def _crear_autoconsum_from_datos_cau(self, cursor, uid, step, dades_cau=None, context=None):
        res = super(GiscedataSwitchingHelpers, self)._crear_autoconsum_from_datos_cau(
            cursor, uid, step, dades_cau, context
        )
        # We're in the same transaction, we can recover the case_ids from memory
        atc_ids = getattr(self, '_tmp_atc_ids', None)

        if atc_ids:
            self._auto_call_wizard_change_state_atr(cursor, uid, atc_ids, 'open')
            self._mark_as_pendent_notificar(cursor, uid, step.header_id.id)
            self._set_cac_as_favorable(cursor, uid, atc_ids)
            self._auto_call_wizard_change_state_atr(cursor, uid, atc_ids, 'done')

        self._tmp_atc_ids = None  # Extra security to avoid strange behavious
        return res

    def _auto_call_wizard_change_state_atr(self, cursor, uid, atc_ids, new_state):
        wiz_obj = self.pool.get('wizard.change.state.atc')
        AGENT_COMER = '06'  # this is harcoded in a lot of places :')

        context = {'active_ids': atc_ids}
        wiz_id = wiz_obj.create(cursor, uid, {'new_state': new_state, 'agent_actual': AGENT_COMER})
        wiz_values = wiz_obj.onchange_agent_actual(
            cursor, uid, [wiz_id], AGENT_COMER)['value']
        wiz_values.update(
            wiz_obj.onchange_new_state(cursor, uid, [wiz_id], new_state, context)['value'])
        wiz_obj.write(cursor, uid, [wiz_id], wiz_values)
        wiz_obj.perform_change(cursor, uid, [wiz_id], context)

    def _mark_as_pendent_notificar(self, cursor, uid, header_id):
        h_obj = self.pool.get('giscedata.switching.step.header')
        h_obj.write(cursor, uid, header_id, {'notificacio_pendent': True})

    def _set_cac_as_favorable(self, cursor, uid, atc_ids):
        atc_obj = self.pool.get("giscedata.atc")
        atc_obj.write(cursor, uid, atc_ids, {'resultat': '01'})  # from TABLA_80 getionatr.defs


GiscedataSwitchingHelpers()
