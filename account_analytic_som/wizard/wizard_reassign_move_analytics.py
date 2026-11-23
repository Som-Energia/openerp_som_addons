# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv, fields
from tools.translate import _


class WizardReassignMoveAnalyticsLine(osv.osv_memory):
    _name = "wizard.reassign.move.analytics.line"
    _description = "Journal item analytic assignment"

    _columns = {
        "wizard_id": fields.many2one("wizard.reassign.move.analytics", "Wizard"),
        "move_line_id": fields.many2one(
            "account.move.line", "Journal item", required=True, readonly=True,
        ),
        "account_id": fields.many2one(
            "account.account", "Account", readonly=True,
        ),
        "name": fields.char("Description", size=256, readonly=True),
        "debit": fields.float("Debit", readonly=True),
        "credit": fields.float("Credit", readonly=True),
        "analytic_account_id": fields.many2one(
            "account.analytic.account", "Analytic account",
            domain=[("type", "=", "normal"), ("state", "!=", "close")],
        ),
    }


WizardReassignMoveAnalyticsLine()


class WizardReassignMoveAnalytics(osv.osv_memory):
    _name = "wizard.reassign.move.analytics"
    _description = "Reassign posted entry analytics"

    def default_get(self, cursor, uid, fields_list, context=None):
        context = context or {}
        move_ids = context.get("active_ids") or (
            [context["active_id"]] if context.get("active_id") else []
        )
        active_model = context.get("active_model") or context.get("from_model", "account.move")
        if active_model != "account.move" or len(move_ids) != 1:
            raise osv.except_osv(
                _("Error"), _("Select exactly one journal entry.")
            )
        move_obj = self.pool.get("account.move")
        move = move_obj._check_analytic_reassignment(
            cursor, uid, move_ids[0], context=context
        )
        values = super(WizardReassignMoveAnalytics, self).default_get(
            cursor, uid, fields_list, context=context
        )
        line_obj = self.pool.get("account.move.line")
        defaults = {
            "move_id": move.id,
            "snapshot": move_obj._analytic_assignment_snapshot(
                cursor, uid, move.id, context=context
            ),
            "line_ids": [(0, 0, {
                "move_line_id": line.id, "account_id": line.account_id.id,
                "name": line.name, "debit": line.debit, "credit": line.credit,
                "analytic_account_id": line.analytic_account_id.id
                or line_obj.get_default_analytic_account(
                    cursor, uid, line.id, context=context
                ),
            }) for line in move.line_id],
        }
        values.update((key, value) for key, value in defaults.items()
                      if key in fields_list)
        return values

    def action_apply(self, cursor, uid, ids, context=None):
        if len(ids) != 1:
            raise osv.except_osv(_("Error"), _("Confirm one reassignment at a time."))
        wizard = self.browse(cursor, uid, ids[0], context=context)
        move_obj = self.pool.get("account.move")
        move_obj._check_analytic_reassignment(
            cursor, uid, wizard.move_id.id, context=context
        )
        if wizard.snapshot != move_obj._analytic_assignment_snapshot(
            cursor, uid, wizard.move_id.id, context=context
        ):
            raise osv.except_osv(
                _("Error"), _("The journal items have changed. Reopen the wizard.")
            )
        assignments = dict(
            (line.move_line_id.id, line.analytic_account_id.id)
            for line in wizard.line_ids
        )
        if len(assignments) != len(wizard.line_ids):
            raise osv.except_osv(_("Error"), _("Duplicate journal items are not allowed."))
        move_obj.apply_analytic_assignments(
            cursor, uid, wizard.move_id.id, assignments, context=context
        )
        return {"type": "ir.actions.act_window_close"}

    _columns = {
        "move_id": fields.many2one(
            "account.move", "Journal entry", required=True, readonly=True,
        ),
        "snapshot": fields.text("Original journal items", readonly=True),
        "line_ids": fields.one2many(
            "wizard.reassign.move.analytics.line", "wizard_id", "Journal items",
        ),
    }


WizardReassignMoveAnalytics()
