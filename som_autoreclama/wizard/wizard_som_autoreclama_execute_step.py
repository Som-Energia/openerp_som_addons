# -*- coding: utf-8 -*-

from osv import osv, fields


class WizardSomAutoreclamaExecuteStep(osv.osv_memory):
    _name = "wizard.som.autoreclama.execute.step"

    def execute_automation_step(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        namespace = context.get("namespace", "atc")

        updtr_obj = self.pool.get("som.autoreclama.state.updater")
        _, _, _, msg, s = updtr_obj.update_items_if_possible(
            cursor, uid, context.get("active_ids", []), namespace, True, context
        )
        msg += "\n\n" + s

        self.write(cursor, uid, ids, {"state": "end", "info": msg})

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text("Informació", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: "",
    }


WizardSomAutoreclamaExecuteStep()
