# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


class WizardAutofactura(osv.osv_memory):
    _name = "wizard.autofactura"

    def do(self, cursor, uid, ids, context=None):
        task_obj = self.pool.get("som.autofactura.task")
        imd_obj = self.pool.get("ir.model.data")
        autofact_id = imd_obj.get_object_reference(
            cursor, uid, "som_autofactura", "som_autofactura_task_facturacio"
        )[1]
        task_obj.action_execute_task(cursor, uid, autofact_id, context)

        return {"type": "ir.actions.act_window_close"}

    def view_tasks(self, cursor, uid, ids, context=None):
        imd_obj = self.pool.get("ir.model.data")
        task_id = imd_obj.get_object_reference(
            cursor, uid, "som_autofactura", "som_autofactura_task_facturacio"
        )[1]
        return {
            "domain": "[('task_id','=', {})]".format(task_id),
            "name": _("Tasques de procés automàtic de facturació"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "som.autofactura.task.step",
            "context": {"active_test": False},
            "type": "ir.actions.act_window",
            "view_id": self.pool.get("ir.ui.view").search(
                cursor, uid, [("name", "=", "som.autofactura.task.step.tree")], context=context
            ),
        }

    _columns = {}


WizardAutofactura()
