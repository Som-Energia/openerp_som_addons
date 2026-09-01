# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields

REFUND_RECTIFY_BATCH_STATUS = [
    ("pending", "Pendent"),
    ("running", "Executant-se"),
    ("blocked", "Bloquejada"),
    ("done", "Finalitzada Ok"),
    ("failed", "Finalitzada Error"),
    ("cancelled", "Cancelada"),
]

REFUND_RECTIFY_BATCH_LINE_STATUS = [
    ("pending", "Pendent"),
    ("running", "Executant-se"),
    ("done", "Finalitzada Ok"),
    ("failed", "Finalitzada Error"),
    ("blocked", "Bloquejada"),
]


class RefundRectifyBatch(osv.osv):
    _name = "refund.rectify.batch"
    _description = "Refund and rectify F1 batch"
    _order = "create_date desc, id desc"

    _columns = {
        "name": fields.char("Reference", size=64, required=True, readonly=True),
        "polissa_id": fields.many2one("giscedata.polissa", "Polissa", required=True, readonly=True),
        "started_at": fields.datetime("Començada", readonly=True),
        "finished_at": fields.datetime("Finalitzada", readonly=True),
        "state": fields.selection(
            REFUND_RECTIFY_BATCH_STATUS, "Estat", required=True, readonly=True
        ),
        "total_lines": fields.integer("F1 totals", readonly=True),
        "completed_lines": fields.integer("F1 completats", readonly=True),
        "failed_lines": fields.integer("F1 erronis", readonly=True),
        "blocked_lines": fields.integer("F1 bloquejats", readonly=True),
        "summary": fields.text("Resum", readonly=True),
        "job_reference": fields.char("Job reference", size=128, readonly=True),
        "line_ids": fields.one2many(
            "refund.rectify.batch.line", "batch_id", "Linies", readonly=True
        ),
    }

    _defaults = {
        "state": lambda *a: "pending",
        "total_lines": lambda *a: 0,
        "completed_lines": lambda *a: 0,
        "failed_lines": lambda *a: 0,
        "blocked_lines": lambda *a: 0,
    }

    def create(self, cursor, uid, vals, context=None):
        batch_id = super(RefundRectifyBatch, self).create(cursor, uid, vals, context=context)
        self.write(cursor, uid, [batch_id], {"name": "F1_R-TASCA-%s" % batch_id}, context=context)
        return batch_id


RefundRectifyBatch()


class RefundRectifyBatchLine(osv.osv):
    _name = "refund.rectify.batch.line"
    _description = "Refund and rectify F1 batch line"
    _order = "batch_id, sequence, id"

    _columns = {
        "batch_id": fields.many2one(
            "refund.rectify.batch", "Tasca", required=True, ondelete="cascade", readonly=True
        ),
        "f1_id": fields.many2one(
            "giscedata.facturacio.importacio.linia", "F1", required=True, readonly=True
        ),
        "sequence": fields.integer("Ordre", required=True, readonly=True),
        "state": fields.selection(
            REFUND_RECTIFY_BATCH_LINE_STATUS, "Estat", required=True, readonly=True
        ),
        "started_at": fields.datetime("Començada", readonly=True),
        "finished_at": fields.datetime("Finalitzada", readonly=True),
        "generated_invoice_ids": fields.many2many(
            "giscedata.facturacio.factura",
            "refund_rectify_batch_line_factura_rel",
            "line_id",
            "factura_id",
            "Factures generades",
            readonly=True,
        ),
        "result": fields.text("Resultat", readonly=True),
        "error": fields.text("Error", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "pending",
    }


RefundRectifyBatchLine()
