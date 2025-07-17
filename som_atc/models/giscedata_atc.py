# -*- coding: utf-8 -*-
from osv import osv, fields
from gestionatr.defs import TABLA_133
from datetime import datetime
import traceback

TIPO_SUBSECCION_SEL = [
    (ac[0], u'[{}] - {}'.format(ac[0], ac[1])) for ac in TABLA_133
]


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

    def case_close_pre_hook(self, cursor, uid, ids, *args):
        if type(ids) not in (list, tuple):
            ids = [ids]
        now = str(datetime.today())
        stack = traceback.extract_stack()
        ps = u"Traça del tancament del cac\n"
        for line in stack:
            ps += u"File '{}', line {}, in {}\n".format(line[0], line[1], line[2])
            ps += u"  " + line[3] + u"\n"
        vars = u"Arguments de crida: "
        for arg in args:
            vars += u"{}, ".format(arg)
        for atc_id in ids:
            track = u"ATC id -> {} de {}\nData execució {}\n{}\n\n{}\n".format(
                atc_id,
                len(ids),
                now,
                vars,
                ps)
            description = self.read(cursor, uid, atc_id, ['description'])['description']
            if description:
                new_msg = u"{}\n\n{}".format(description, track)
            else:
                new_msg = track
            self.write(cursor, uid, atc_id, {'description': new_msg})

        return super(GiscedataAtc, self).case_close_pre_hook(cursor, uid, ids, *args)

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
            "tipus_subseccio",
            type="selection",
            selection=TIPO_SUBSECCION_SEL,
            string="tipus autoconsum",
            readonly=True,
        ),
        "collectiu": fields.related(
            "polissa_id",
            "is_autoconsum_collectiu",
            type="boolean",
            string="Col·lectiu",
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
