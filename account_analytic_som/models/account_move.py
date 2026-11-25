# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json

from osv import osv
from tools.translate import _


class AccountMove(osv.osv):
    _name = "account.move"
    _inherit = "account.move"

    def _check_analytic_reassignment(self, cursor, uid, move_id, context=None):
        self.check_perm(cursor, uid, "write", raise_exception=True, context=context)
        if not self.search(cursor, uid, [("id", "=", move_id)], context=context):
            raise osv.except_osv(_("Error"), _("The journal entry is not accessible."))
        move = self.browse(cursor, uid, move_id, context=context)
        if move.state != "posted" or not move.line_id or any(
            line.state != "valid" for line in move.line_id
        ):
            raise osv.except_osv(
                _("Error"), _("Select a posted entry with valid journal items.")
            )
        return move

    def _analytic_assignment_snapshot(self, cursor, uid, move_id, context=None):
        line_obj = self.pool.get("account.move.line")
        line_ids = line_obj.search(
            cursor, uid, [("move_id", "=", move_id)], order="id", context=context
        )
        values = line_obj.read(cursor, uid, line_ids, [
            "account_id", "partner_id", "product_id", "date", "name",
            "debit", "credit", "analytic_account_id", "analytics_id",
        ], context=context)
        return json.dumps(sorted(values, key=lambda line: line["id"]), sort_keys=True)

    def apply_analytic_assignments(
        self, cursor, uid, move_id, assignments, context=None
    ):
        """Apply one complete entry's line-ID -> analytic-ID choices locally.

        Empty choices resolve current defaults. Integration addons may inherit
        this method and enqueue their remote operation after super() succeeds.
        No posting, reconciliation or remote synchronization is performed here.
        """
        move = self._check_analytic_reassignment(
            cursor, uid, move_id, context=context
        )
        if set(assignments) != set(line.id for line in move.line_id):
            raise osv.except_osv(
                _("Error"), _("Provide each journal item exactly once.")
            )
        line_obj = self.pool.get("account.move.line")
        analytic_obj = self.pool.get("account.analytic.account")
        changes = {}
        for line in move.line_id:
            analytic_id = assignments[line.id] or line_obj.get_default_analytic_account(
                cursor, uid, line.id, context=context
            )
            if analytic_id:
                allowed_ids = analytic_obj.search(cursor, uid, [
                    ("id", "=", analytic_id), ("type", "=", "normal"),
                    ("state", "!=", "close"),
                    ("company_id", "in", [False, line.account_id.company_id.id]),
                ], context=context)
                if not allowed_ids:
                    raise osv.except_osv(
                        _("Error"),
                        _("Choose an available analytic account for the entry's company."),
                    )
            if analytic_id != line.analytic_account_id.id:
                if line.analytics_id:
                    raise osv.except_osv(
                        _("Error"),
                        _("Items with an analytic distribution cannot be reassigned "
                          "to a single analytic account using this wizard."),
                    )
                if analytic_id and not line.journal_id.analytic_journal_id:
                    raise osv.except_osv(
                        _("Error"), _("Configure an analytic journal before reassigning.")
                    )
                changes.setdefault(analytic_id, []).append(line.id)
        for analytic_id, line_ids in changes.items():
            # Standard write validates the entry and rebuilds its analytic lines.
            # Only this field is written: posted state and reconciliations remain.
            line_obj.write(cursor, uid, line_ids, {
                "analytic_account_id": analytic_id,
            }, context=context)
        return True


AccountMove()
