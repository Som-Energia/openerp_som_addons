# -*- coding: utf-8 -*-
import json

from osv import osv, fields, orm
from tools.translate import _
from gestionatr.defs import (
    TABLA_8,
    TIPUS_DOCUMENT_INST_CIE,
    TABLA_64,
    TABLA_62,
    SINO,
    TABLA_117,
)


class GiscedataSwitchingWizardA301(osv.osv_memory):

    _inherit = "giscedata.switching.a301.wizard"

    def _get_necessita_documentacio_tecnica(self, cursor, uid, context=None):
        if context is None:
            context = {}
        res = False
        pol_id = context.get("contract_id", context.get("active_id"))
        if pol_id:
            distri = self.pool.get("giscedata.polissa").read(
                cursor, uid, pol_id, ["distribuidora"]
            )["distribuidora"]
            if distri:
                dcode = self.pool.get("res.partner").read(
                    cursor, uid, distri[0], ["ref"]
                )["ref"]
                res = dcode in ["0021", "0022"]
        return res

    _columns = {
        "necessita_documentacio_tecnica": fields.boolean(
            string="Necessita Documentació Tecnica", type="boolean"
        )
    }

    _defaults = {"necessita_documentacio_tecnica": _get_necessita_documentacio_tecnica}


GiscedataSwitchingWizardA301()
