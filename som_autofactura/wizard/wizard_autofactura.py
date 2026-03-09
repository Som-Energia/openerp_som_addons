# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _
from rq.job import Job
from rq.registry import StartedJobRegistry
from oorq.oorq import setup_redis_connection


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

    def unlock(self, cursor, uid, ids, context=None):
        redis_conn = setup_redis_connection()
        jobs_ids = StartedJobRegistry('background_autofactura', connection=redis_conn).get_job_ids()

        if len(jobs_ids) == 0:
            raise osv.except_osv(
                _('Error'),
                _("No hi ha cap procés automàtic de facturació en execució")
            )

        if len(jobs_ids) > 1:
            raise osv.except_osv(
                _('Error'),
                _("Hi han més d'una tasca en execució, contacta amb IT")
            )

        if len(jobs_ids) == 1:
            job = Job.fetch(jobs_ids[0], connection=redis_conn)
            job.delete()

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
