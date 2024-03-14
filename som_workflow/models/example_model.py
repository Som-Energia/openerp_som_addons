# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
import netsvc

_STATES = [
    ("draft", "Draft"),
    ("open", "Open"),
    ("paid", "Paid"),
    ("unpaid", "Unpaid"),
    ("refund", "Refund"),
    ("cancel", "Cancel"),
]


class ExampleModel(osv.osv):
    _name = "example.model"

    def send_signal(self, cursor, uid, ids, signals):
        wf_service = netsvc.LocalService("workflow")
        if not isinstance(signals, list) and not isinstance(signals, tuple):
            signals = [signals]
        for record_id in ids:
            for signal in signals:
                wf_service.trg_validate(uid, "example.model", record_id, signal, cursor)
        return True

    def log_message(self, cursor, uid, ids, message, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            record.write({"log": ("{}{}: {}\n").format(record.log, datetime.now(), message)})

    _columns = {
        "name": fields.char(
            "Name",
            size=256,
            required=True,
        ),
        "state": fields.selection(
            _STATES,
            "State",
            readonly=True,
            required=True,
        ),
        "partner_id": fields.many2one(
            "res.partner",
            "Partner",
            states={
                "open": [("required", True)],
            },
        ),
        "amount_total": fields.integer(
            "Amount total",
            readonly=True,
            states={
                "draft": [("readonly", False)],
                "open": [("readonly", False)],
            }
        ),
        "paid": fields.boolean(
            "Paid",
            readonly=True,
            states={
                "draft": [("readonly", False)],
                "open": [("readonly", False)],
                "unpaid": [("readonly", False)],
            },
        ),
        "log": fields.text(
            "Log",
            size=256,
            readonly=True,
        ),
    }

    _defaults = {
        "state": lambda *a: "draft",
        "log": lambda *a: "",
    }


ExampleModel()
