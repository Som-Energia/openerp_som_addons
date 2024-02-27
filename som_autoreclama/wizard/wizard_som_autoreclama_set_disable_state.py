# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardSomAutoreclamaSetDisableState(osv.osv_memory):
    _name = "wizard.som.autoreclama.set.disable.state"

    def assign_state(self, cursor, uid, ids, context=None):
        namespace = context.get("namespace", "atc")
        h_obj = self.pool.get("som.autoreclama.state.history." + namespace)

        item_ids = context.get("active_ids", [])

        ir_obj = self.pool.get("ir.model.data")
        disable_state_id = ir_obj.get_object_reference(
            cursor, uid, "som_autoreclama", "disabled_state_workflow_" + namespace
        )[1]
        s_obj = self.pool.get("som.autoreclama.state")
        next_state_id = s_obj.browse(cursor, uid, disable_state_id)

        info = ""
        for item_id in item_ids:
            try:
                h_obj.historize(cursor, uid, item_id, next_state_id.id, None, False, context)
                info += _("{} {} estat canviat manualment a '{}'\n").format(
                    namespace.capitalize(), item_id, next_state_id.name
                )
            except Exception as e:
                info += _("{} {} error al canviar manualment a '{}' : {}\n").format(
                    namespace.capitalize(), item_id, next_state_id.name, e.message
                )

        self.write(cursor, uid, ids, {"state": "end", "info": info})
        return True

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text("Informació", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: "",
    }


WizardSomAutoreclamaSetDisableState()
