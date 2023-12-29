# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardSomAutoreclamaSetManualState(osv.osv_memory):
    _name = "wizard.som.autoreclama.set.manual.state"

    def _get_workflow_id(self, cursor, uid, context=None):
        namespace = context.get("namespace", "atc")
        ir_obj = self.pool.get("ir.model.data")
        return ir_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "workflow_" + namespace
        )[1]

    def assign_state(self, cursor, uid, ids, context=None):
        namespace = context.get("namespace", "atc")
        h_obj = self.pool.get("som.autoreclama.state.history." + namespace)

        item_ids = context.get("active_ids", [])

        wiz = self.browse(cursor, uid, ids[0], context)

        info = ""
        for item_id in item_ids:
            try:
                h_obj.historize(cursor, uid, item_id, wiz.next_state_id.id, None, False, context)
                info += _("{} {} estat canviat manualment a '{}'\n").format(
                    namespace.capitalize(), item_id, wiz.next_state_id.name
                )
            except Exception as e:
                info += _("{} {} error al canviar manualment a '{}' : {}\n").format(
                    namespace.capitalize(), item_id, wiz.next_state_id.name, e.message
                )

        self.write(cursor, uid, ids, {"state": "end", "info": info})
        return True

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text("Informació", readonly=True),
        "workflow_id": fields.many2one("som.autoreclama.state.workflow", "Fluxe"),
        "next_state_id": fields.many2one(
            "som.autoreclama.state",
            "Estat",
            required=True,
            domain="[('workflow_id', '=', workflow_id)]"
        ),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: "",
        "workflow_id": _get_workflow_id,
    }


WizardSomAutoreclamaSetManualState()
