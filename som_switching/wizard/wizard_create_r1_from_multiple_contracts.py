# -*- coding: utf-8 -*-
from datetime import datetime
import json

from osv import osv, fields, orm
from tools.translate import _
from gestionatr.defs import TABLA_81
from gestionatr.input.messages.R1 import get_minimum_fields


class WizardR101FromMultipleContracts(osv.osv_memory):
    _name = "wizard.r101.from.multiple.contracts"
    _inherit = "wizard.r101.from.multiple.contracts"

    def create_r1_from_contracts(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        ctx = context.copy()
        info = self.read(
            cursor, uid, ids, ["facturacio_suspesa", "refacturacio_pendent"], context=context
        )[0]
        info.pop("id")
        ctx.update({"extra_r1_vals": info})

        res = super(WizardR101FromMultipleContracts, self).create_r1_from_contracts(
            cursor, uid, ids, context=ctx
        )

        return res

    def onchange_subtipus(self, cursor, uid, ids, subtipus, context=None):
        if context is None:
            context = {}
        res = super(WizardR101FromMultipleContracts, self).onchange_subtipus(
            cursor, uid, ids, subtipus, context=context
        )
        if subtipus:
            subtipus_obj = self.pool.get("giscedata.subtipus.reclamacio")
            subinfo = subtipus_obj.read(cursor, uid, subtipus, ["name"], context=context)
            if subinfo["name"] in ("036", "009"):
                res["value"].update({"facturacio_suspesa": True, "refacturacio_pendent": True})
        return res

    _columns = {
        "facturacio_suspesa": fields.boolean("Marcar contracte amb facturació suspesa"),
        "refacturacio_pendent": fields.boolean("Marcar contracte amb refacturacio pendent"),
    }


WizardR101FromMultipleContracts()
