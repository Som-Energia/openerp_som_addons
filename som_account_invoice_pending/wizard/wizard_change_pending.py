# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
from tools.translate import _


class WizardChangePending(osv.osv_memory):
    """Wizard for changing pending state in invoices"""

    _inherit = "wizard.change.pending"

    def onchange_new_pending(self, cursor, uid, ids, new_pending):
        pending_obj = self.pool.get("account.invoice.pending.state")

        pending_days = pending_obj.read(cursor, uid, new_pending, ["pending_days"])["pending_days"]

        return {
            "value": {"new_pending_days": pending_days},
            "domain": {},
            "warning": {},
        }

    def action_set_new_pending_remember_days(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wizard = self.browse(cursor, uid, ids[0])
        self._validate_wizard(wizard)

        model_ids = context.get("active_ids", [])
        new_pending_id = wizard.new_pending.id

        default_pending_state_days = self._get_default_pending_state_days(
            cursor, uid, new_pending_id
        )

        for model_id in model_ids:
            invoice_id = self._get_invoice_id_from_gff(cursor, uid, model_id, context)
            pending_state_days = self._calculate_pending_state_days(
                cursor, uid, new_pending_id, default_pending_state_days, invoice_id
            )

            self._set_pending_state_with_calculated_days(
                cursor, uid, new_pending_id, model_id, invoice_id, pending_state_days, context
            )

        wizard.write({"changed_invoices": len(model_ids), "state": "end"})

    def _validate_wizard(self, wizard):
        if not wizard.new_pending:
            raise osv.except_osv(
                _("Error!"),
                _(
                    "If you want to change the pending state"
                    ' the "new pending" field must be filled up'
                ),
            )

    def _get_default_pending_state_days(self, cursor, uid, new_pending_id):
        pstate_obj = self.pool.get("account.invoice.pending.state")

        default_pending_state_days = pstate_obj.read(cursor, uid, new_pending_id, ["pending_days"])[
            "pending_days"
        ]

        return default_pending_state_days

    def _get_invoice_id_from_gff(self, cursor, uid, model_id, context):
        #  invoice id is a tuple with (ID,NAME), and we need only the ID
        model_obj = self.pool.get(context["model"])
        return model_obj.read(cursor, uid, model_id, ["invoice_id"])["invoice_id"][0]

    def _calculate_pending_state_days(
        self, cursor, uid, new_pending_id, default_pending_state_days, invoice_id
    ):
        _FIELDS_TO_READ = [
            "pending_state_id",
            "change_date",
            "invoice_id",
            "days_to_next_state",
            "end_date",
        ]
        pending_history_obj = self.pool.get("account.invoice.pending.history")

        pending_state_days = default_pending_state_days
        pending_history_ids = pending_history_obj.search(
            cursor,
            uid,
            [("pending_state_id", "=", new_pending_id), ("invoice_id", "=", invoice_id)],
            order="change_date desc",
        )
        if pending_history_ids:
            last_history_in_same_state = pending_history_obj.read(
                cursor, uid, pending_history_ids[0], _FIELDS_TO_READ
            )
            if last_history_in_same_state["end_date"]:
                days_in_prev_state = (
                    datetime.strptime(last_history_in_same_state["end_date"], "%Y-%m-%d")
                    - datetime.strptime(last_history_in_same_state["change_date"], "%Y-%m-%d")
                ).days
                pending_state_days = pending_state_days - days_in_prev_state
        return pending_state_days

    def _set_pending_state_with_calculated_days(
        self, cursor, uid, new_pending_id, model_id, invoice_id, pending_state_days, context
    ):
        model_obj = self.pool.get(context["model"])
        pending_history_obj = self.pool.get("account.invoice.pending.history")

        model_obj.set_pending(cursor, uid, [model_id], new_pending_id, context=context)
        pending_history_records = pending_history_obj.search(
            cursor, uid, [("invoice_id", "=", invoice_id)]
        )
        if pending_history_records:
            # We consider the last record the first one due to order
            # statement in the model definition.
            pending_history_obj.write(
                cursor, uid, pending_history_records[0], {"days_to_next_state": pending_state_days}
            )

    _columns = {
        "new_pending_days": fields.integer(u"Dies pendents del nou estat"),
    }

    _defaults = {
        "new_pending_days": lambda *a: 0,
    }


WizardChangePending()
