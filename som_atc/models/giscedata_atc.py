# -*- coding: utf-8 -*-
from osv import osv, fields

from giscedata_polissa.giscedata_polissa import TIPO_AUTOCONSUMO_SEL


class GiscedataAtc(osv.osv):

    _name = "giscedata.atc"
    _inherit = "giscedata.atc"

    def _ff_get_process_step(self, cursor, uid, ids, field_name, arg, context):
        return super(GiscedataAtc, self)._ff_get_process_step(
            cursor, uid, ids, field_name, arg, context
        )

    def _trg_switching(self, cursor, uid, ids, context=None):
        """
        Funció per especificar els IDs a recalcular
        """
        sw_obj = self.pool.get("giscedata.switching")
        sw_vals = sw_obj.read(cursor, uid, ids, ["ref", "ref2"])
        atc_ids = []
        for sw_val in sw_vals:
            if sw_val["ref"] and sw_val["ref"].split(",")[0] == "giscedata.atc":
                atc_ids.append(int(sw_val["ref"].split(",")[1]))
            elif sw_val["ref2"] and sw_val["ref2"].split(",")[0] == "giscedata.atc":
                atc_ids.append(int(sw_val["ref2"].split(",")[1]))
        return atc_ids

    _columns = {
        "tarifa": fields.related(
            "polissa_id",
            "llista_preu",
            "name",
            type="char",
            string="tarifa Comercialitzadora",
            readonly=True,
        ),
        "tipus_autoconsum": fields.related(
            "polissa_id",
            "autoconsumo",
            type="selection",
            selection=TIPO_AUTOCONSUMO_SEL,
            string="tipus autoconsum",
            readonly=True,
        ),
        "te_generation": fields.related(
            "polissa_id",
            "te_assignacio_gkwh",
            type="boolean",
            string="te generation",
            readonly=True,
        ),
        "pending_state": fields.related(
            "polissa_id", "pending_state", type="char", string="pending state", readonly=True
        ),
        "polissa_active": fields.related(
            "polissa_id", "active", type="boolean", string="polissa activa", readonly=True
        ),
        "process_step": fields.function(
            _ff_get_process_step,
            method=True,
            string=u"Pas del R1",
            type="char",
            size=10,
            store={
                "giscedata.atc": (
                    lambda self, cr, uid, ids, c={}: ids,
                    ["ref", "ref2", "history_line"],
                    10,
                ),
                "giscedata.switching": (_trg_switching, ["step_id", "step_ids"], 10),
            },
        ),
    }


GiscedataAtc()
