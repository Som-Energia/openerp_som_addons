# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64
import hashlib
import json

from osv import fields, osv
from tools.translate import _


IMMUTABLE_FIELDS = frozenset([
    "request_key",
    "polissa_id",
    "cups",
    "owner_change_type",
    "payload",
    "payload_hash",
    "m101_pdf",
    "m101_pdf_hash",
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
    _rec_name = "request_key"

    def _payload_hash(self, payload):
        serialized = json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(serialized).hexdigest()

    def create(self, cursor, uid, values, context=None):
        values = values.copy()
        values["payload_hash"] = self._payload_hash(values.get("payload", {}))
        return super(SomHolderChangeRequest, self).create(
            cursor, uid, values, context=context
        )

    def create_or_get(self, cursor, uid, values, context=None):
        request_key = values.get("request_key")
        request_ids = self.search(
            cursor,
            uid,
            [("request_key", "=", request_key)],
            limit=1,
            context=context,
        )
        if not request_ids:
            return self.create(cursor, uid, values, context=context)

        request = self.read(
            cursor,
            uid,
            request_ids[0],
            ["payload_hash"],
            context=context,
        )
        payload_hash = self._payload_hash(values.get("payload", {}))
        if request["payload_hash"] != payload_hash:
            raise osv.except_osv(
                _("Idempotency conflict"),
                _("The request key already exists with a different payload."),
            )
        return request_ids[0]

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

    def freeze_m101(self, cursor, uid, request_id, pdf, context=None):
        if isinstance(request_id, (list, tuple)):
            if len(request_id) != 1:
                raise osv.except_osv(
                    _("Invalid holder change"),
                    _("Exactly one request is required to freeze the M101."),
                )
            request_id = request_id[0]

        pdf_hash = hashlib.sha256(pdf).hexdigest()
        request = self.read(
            cursor,
            uid,
            request_id,
            ["m101_pdf_hash"],
            context=context,
        )
        if request["m101_pdf_hash"]:
            if request["m101_pdf_hash"] != pdf_hash:
                raise osv.except_osv(
                    _("Frozen M101 conflict"),
                    _("The request already has a different frozen M101."),
                )
            return True

        return super(SomHolderChangeRequest, self).write(
            cursor,
            uid,
            [request_id],
            {
                "m101_pdf": base64.b64encode(pdf),
                "m101_pdf_hash": pdf_hash,
            },
            context=context,
        )

    _columns = {
        "request_key": fields.char(
            "Request key", size=128, required=True, readonly=True, select=True
        ),
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
        "payload_hash": fields.char(
            "Payload hash", size=64, required=True, readonly=True, select=True
        ),
        "m101_pdf": fields.binary("Frozen M101", readonly=True),
        "m101_pdf_hash": fields.char(
            "Frozen M101 hash", size=64, readonly=True, select=True
        ),
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

    _sql_constraints = [
        (
            "request_key_unique",
            "unique(request_key)",
            "The holder change request key must be unique.",
        ),
    ]

    _order = "id desc"


SomHolderChangeRequest()
