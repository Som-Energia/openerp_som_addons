# -*- coding: utf-8 -*-

from osv import osv
from tools.translate import _


class WizardSomAutoreclamaGeneratedAtc(osv.osv_memory):
    _name = "wizard.som.autoreclama.generated.atc"

    def view_generated_atc(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        namespace = context.get("namespace", "atc")
        h_obj = self.pool.get("som.autoreclama.state.history." + namespace)

        model_obj = self.pool.get("giscedata." + namespace)

        item_ids = context.get("active_ids", [])
        generated_atc_ids = []

        for item_id in item_ids:
            h_ids = model_obj.read(
                cursor,
                uid,
                item_id,
                ["autoreclama_history_ids"],
                context=context
            )["autoreclama_history_ids"]
            for h_id in h_ids:
                h_data = h_obj.read(cursor, uid, h_id, ["generated_atc_id"], context=context)
                if "generated_atc_id" in h_data and h_data["generated_atc_id"]:
                    generated_atc_ids.append(h_data["generated_atc_id"][0])

        return {
            "domain": "[('id','in', {0})]".format(str(generated_atc_ids)),
            "name": _("Casos ATC automatics creats"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "giscedata.atc",
            "type": "ir.actions.act_window",
        }

    _columns = {}

    _defaults = {}


WizardSomAutoreclamaGeneratedAtc()
