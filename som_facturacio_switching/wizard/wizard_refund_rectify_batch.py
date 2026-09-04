# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields
from tools.translate import _


class WizardRefundRectifyBatch(osv.osv_memory):
    _name = "wizard.refund.rectify.batch"
    _description = "Create refund and rectify F1 batch"

    def create_batch(self, cursor, uid, ids, context=None):
        context = context or {}
        active_ids = context.get("active_ids", [])
        batch_obj = self.pool.get("refund.rectify.batch")
        batch_id = batch_obj.create_batch(cursor, uid, active_ids, context=context)
        batch_obj.schedule_batch_execution(cursor, uid, batch_id, context=context)

        return {
            "type": "ir.actions.act_window",
            "name": _("Lot pendent d'abonar i rectificar"),
            "res_model": "refund.rectify.batch",
            "view_type": "form",
            "view_mode": "form",
            "res_id": batch_id,
            "target": "current",
        }

    _columns = {
        "info": fields.text("Information", readonly=True),
    }

    _defaults = {
        "info": lambda *a: _(
            "Es crearà una tasca pendent amb els F1 seleccionats."
        ),
    }


WizardRefundRectifyBatch()
