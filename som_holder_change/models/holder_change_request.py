# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from osv import fields, osv
from tools.translate import _


IMMUTABLE_FIELDS = frozenset([
    "polissa_id",
    "cups",
    "owner_change_type",
    "payload",
])

REQUEST_STATES = [
    ("received", "Received"),
    ("prevalidating", "Prevalidating"),
    ("validation_error", "Validation error"),
    ("awaiting_signature", "Awaiting signature"),
    ("signed", "Signed"),
    ("queued", "Queued"),
    ("processing", "Processing"),
    ("completed", "Completed"),
    ("execution_error", "Execution error"),
    ("review_required", "Review required"),
    ("declined", "Declined"),
    ("expired", "Expired"),
    ("cancelled", "Cancelled"),
]


class SomHolderChangeRequest(osv.osv):
    _name = "som.holder.change.request"
    _description = "Holder change request"
    _rec_name = "cups"

    def write(self, cursor, uid, ids, values, context=None):
        immutable = IMMUTABLE_FIELDS.intersection(values)
        if immutable:
            raise osv.except_osv(
                _("Immutable request"),
                _("The holder change request identity and payload cannot be modified."),
            )
        return super(SomHolderChangeRequest, self).write(
            cursor, uid, ids, values, context=context
        )

    _columns = {
        "polissa_id": fields.many2one(
            "giscedata.polissa",
            "Contract",
            required=True,
            readonly=True,
            ondelete="restrict",
        ),
        "cups": fields.char(
            "CUPS", size=22, required=True, readonly=True, select=True
        ),
        "owner_change_type": fields.selection(
            [("T", "Transfer"), ("S", "Subrogation")],
            "Holder change type",
            required=True,
            readonly=True,
        ),
        "payload": fields.json("Request payload", required=True, readonly=True),
        "state": fields.selection(
            REQUEST_STATES, "State", required=True, readonly=True, select=True
        ),
        "signature_process_id": fields.many2one(
            "giscedata.signatura.process",
            "Signature process",
            readonly=True,
            ondelete="restrict",
        ),
        "switching_id": fields.many2one(
            "giscedata.switching",
            "M1 case",
            readonly=True,
            ondelete="restrict",
        ),
        "result_polissa_id": fields.many2one(
            "giscedata.polissa",
            "Result contract",
            readonly=True,
            ondelete="restrict",
        ),
        "attempt_count": fields.integer("Execution attempts", readonly=True),
        "last_attempt_at": fields.datetime("Last attempt", readonly=True),
        "error_code": fields.char("Error code", size=64, readonly=True),
        "error_message": fields.text("Error message", readonly=True),
    }

    _defaults = {
        "state": lambda *args: "received",
        "attempt_count": lambda *args: 0,
    }

    _order = "id desc"


SomHolderChangeRequest()
