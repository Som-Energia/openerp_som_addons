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
        if not active_ids:
            raise osv.except_osv(_("Error"), _("Cal seleccionar almenys un F1."))

        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        f1_data = f1_obj.read(cursor, uid, active_ids, ["polissa_id"])
        polissa_names = []
        polissa_ids = []
        for f1_d in f1_data:
            if f1_d["polissa_id"]:
                polissa_names.append(f1_d["polissa_id"][1])
                polissa_ids.append(f1_d["polissa_id"][0])

        polissa_ids = list(set(polissa_ids))
        polissa_names = list(set(polissa_names))

        if len(polissa_ids) == 0:
            raise osv.except_osv(
                _("Error"), _("Els F1 seleccionats no tenen cap pòlissa associada."),
            )
        if len(polissa_ids) > 1:
            raise osv.except_osv(
                _("Error"),
                _("Els F1 seleccionats han de correspondre a una única pòlissa.")
                + _("\nPolisses trobades: ") + ", ".join(polissa_names),
            )

        ordered_f1_ids = f1_obj.search(
            cursor, uid, [("id", "in", active_ids)], order="fecha_factura_desde asc, id asc"
        )
        batch_obj = self.pool.get("refund.rectify.batch")
        batch_id = batch_obj.create(
            cursor,
            uid,
            {
                "name": "/",
                "polissa_id": polissa_ids[0],
                "total_lines": len(ordered_f1_ids),
                "summary": _("Tasca pendent creada. Encara no s'ha iniciat cap refacturació."),
            },
            context=context,
        )
        line_obj = self.pool.get("refund.rectify.batch.line")
        for sequence, f1_id in enumerate(ordered_f1_ids, 1):
            line_obj.create(
                cursor,
                uid,
                {"batch_id": batch_id, "f1_id": f1_id, "sequence": sequence},
                context=context,
            )

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
