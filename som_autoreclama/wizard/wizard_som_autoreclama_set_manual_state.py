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

    def _get_associated_polissa_id(self, cursor, uid, context=None):
        namespace = context.get("namespace", "atc")
        if namespace == "atc":
            item_ids = context.get("active_ids", [])
            atc_obj = self.pool.get("giscedata.atc")
            datas = atc_obj.read(cursor, uid, item_ids, ['polissa_id'])
            return list(set([data['polissa_id'][0] for data in datas]))[0]
        elif namespace in ["polissa", "polissa009"]:
            return context["active_ids"][0]
        return None

    def _get_associated_subtipus_name(self, cursor, uid, context=None):
        namespace = context.get("namespace", "atc")
        if namespace == "atc":
            return '029'
        elif namespace == "polissa":
            return '006'
        elif namespace == "polissa009":
            return '009'
        return ''

    def assign_state(self, cursor, uid, ids, context=None):
        namespace = context.get("namespace", "atc")
        h_obj = self.pool.get("som.autoreclama.state.history." + namespace)

        item_ids = context.get("active_ids", [])

        wiz = self.browse(cursor, uid, ids[0], context)

        info = ""
        for item_id in item_ids:
            try:
                h_obj.historize(
                    cursor, uid,
                    item_id,
                    wiz.next_state_id.id,
                    wiz.change_date,
                    wiz.attached_atc.id,
                    context
                )
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
        "as_polissa_id": fields.many2one("giscedata.polissa"),
        "as_subtipus_name": fields.text("subtipus"),
        "workflow_id": fields.many2one("som.autoreclama.state.workflow", "Fluxe"),
        "next_state_id": fields.many2one(
            "som.autoreclama.state",
            "Estat",
            required=True,
            domain="[('workflow_id', '=', workflow_id)]"
        ),
        "attached_atc": fields.many2one(
            "giscedata.atc",
            "Cas ATC associat",
            domain="[('polissa_id', '=', as_polissa_id), ('subtipus_id.name', '=', as_subtipus_name)]",  # noqa: E501
        ),
        "change_date": fields.date("Canvi de data"),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: "",
        "workflow_id": _get_workflow_id,
        "as_polissa_id": _get_associated_polissa_id,
        "as_subtipus_name": _get_associated_subtipus_name,
    }


WizardSomAutoreclamaSetManualState()
