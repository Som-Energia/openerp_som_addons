# -*- coding: utf-8 -*-
from __future__ import absolute_import

import mock
import os
from destral import testing
from osv import osv
from six import exec_
from tools import config


class TestAnalyticReassignment(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestAnalyticReassignment, self).setUp()
        self.move_obj = self.openerp.pool.get("account.move")
        self.line_obj = self.openerp.pool.get("account.move.line")
        self.wizard_obj = self.openerp.pool.get("wizard.reassign.move.analytics")
        self.analytic_obj = self.openerp.pool.get("account.analytic.account")
        self.default_obj = self.openerp.pool.get("account.analytic.default")
        self.default_obj.unlink(
            self.cursor, self.uid,
            self.default_obj.search(self.cursor, self.uid, []),
        )
        self.analytic_id = self.analytic_obj.create(
            self.cursor, self.uid, {"name": "Reassignment analytic"}
        )
        self.other_analytic_id = self.analytic_obj.create(
            self.cursor, self.uid, {"name": "Replacement analytic"}
        )
        self.account_id = self.openerp.pool.get("account.account").search(
            self.cursor, self.uid,
            [("type", "not in", ["view", "closed"]), ("currency_id", "=", False)],
            limit=1,
        )[0]
        journal_obj = self.openerp.pool.get("account.journal")
        data_obj = self.openerp.pool.get("ir.model.data")
        view_id = data_obj.get_object_reference(
            self.cursor, self.uid, "account", "account_journal_view"
        )[1]
        sequence_id = data_obj.get_object_reference(
            self.cursor, self.uid, "account", "sequence_journal"
        )[1]
        self.journal_id = journal_obj.create(
            self.cursor, self.uid, {
                "name": "Reassignment journal", "code": "REASSIGN",
                "type": "general", "view_id": view_id,
                "sequence_id": sequence_id,
            },
        )
        analytic_journal_id = self.openerp.pool.get("account.analytic.journal").create(
            self.cursor, self.uid,
            {"name": "Reassignment", "code": "REA", "type": "general"},
        )
        journal_obj.write(
            self.cursor, self.uid, [self.journal_id],
            {"analytic_journal_id": analytic_journal_id},
        )
        period_obj = self.openerp.pool.get("account.period")
        fiscalyear_id = self.openerp.pool.get("account.fiscalyear").create(
            self.cursor, self.uid, {
                "name": "Reassignment year", "code": "REASSIGN",
                "date_start": "2026-01-01", "date_stop": "2026-12-31",
            },
        )
        period_id = period_obj.create(
            self.cursor, self.uid, {
                "name": "Reassignment period", "code": "REA01",
                "date_start": "2026-01-01", "date_stop": "2026-01-31",
                "fiscalyear_id": fiscalyear_id,
            },
        )
        self.date = period_obj.browse(self.cursor, self.uid, period_id).date_start
        self.move_id = self.move_obj.create(
            self.cursor, self.uid, {
                "journal_id": self.journal_id, "period_id": period_id,
                "date": self.date,
                "line_id": [(0, 0, {
                    "name": "Reassignment", "account_id": self.account_id,
                    "partner_id": data_obj.get_object_reference(
                        self.cursor, self.uid, "base", "res_partner_agrolait"
                    )[1],
                    "date": self.date, "debit": debit, "credit": credit,
                }) for debit, credit in [(100, 0), (0, 100)]],
            },
        )
        self.move_obj.post(self.cursor, self.uid, [self.move_id])
        self.line_ids = self.line_obj.search(
            self.cursor, self.uid, [("move_id", "=", self.move_id)], order="id"
        )
        self.context = {
            "active_model": "account.move", "active_ids": [self.move_id],
        }

    def _wizard(self):
        values = self.wizard_obj.default_get(
            self.cursor, self.uid, ["move_id", "line_ids", "snapshot"],
            context=self.context,
        )
        return self.wizard_obj.create(
            self.cursor, self.uid, values, context=self.context
        )

    def _assignments(self, analytic_id):
        return dict((line_id, analytic_id) for line_id in self.line_ids)

    def _default(self):
        return self.default_obj.create(
            self.cursor, self.uid, {
                "account_id": self.account_id, "analytic_id": self.analytic_id,
                "date_start": self.date, "date_stop": self.date,
            },
        )

    def test_prefill_explicit_then_default_without_writing(self):
        self._default()
        self.line_obj.write(
            self.cursor, self.uid, [self.line_ids[0]],
            {"analytic_account_id": self.other_analytic_id},
        )
        wizard_id = self._wizard()
        wizard = self.wizard_obj.browse(self.cursor, self.uid, wizard_id)
        proposals = dict(
            (line.move_line_id.id, line.analytic_account_id.id)
            for line in wizard.line_ids
        )
        self.assertEqual(proposals[self.line_ids[0]], self.other_analytic_id)
        self.assertEqual(proposals[self.line_ids[1]], self.analytic_id)
        source = self.line_obj.browse(self.cursor, self.uid, self.line_ids[1])
        self.assertFalse(source.analytic_account_id)

    def test_blank_uses_default_and_rebuilds_analytics_without_reposting(self):
        self._default()
        self.move_obj.apply_analytic_assignments(
            self.cursor, self.uid, self.move_id, self._assignments(False)
        )
        move = self.move_obj.browse(self.cursor, self.uid, self.move_id)
        self.assertEqual(move.state, "posted")
        for line in move.line_id:
            self.assertEqual(line.analytic_account_id.id, self.analytic_id)
            self.assertEqual(len(line.analytic_lines), 1)
            self.assertEqual(line.analytic_lines[0].account_id.id, self.analytic_id)
            self.assertEqual(
                line.analytic_lines[0].amount, line.credit - line.debit
            )

    def test_replace_then_clear_without_default_preserves_accounting(self):
        fields = [
            "account_id", "partner_id", "debit", "credit", "date", "move_id",
            "reconcile_id", "reconcile_partial_id", "state",
        ]
        before = self.line_obj.read(self.cursor, self.uid, self.line_ids, fields)
        for analytic_id in [self.analytic_id, self.other_analytic_id, False]:
            self.move_obj.apply_analytic_assignments(
                self.cursor, self.uid, self.move_id,
                self._assignments(analytic_id),
            )
            for line in self.line_obj.browse(self.cursor, self.uid, self.line_ids):
                self.assertEqual(line.analytic_account_id.id, analytic_id)
                self.assertEqual(len(line.analytic_lines), 1 if analytic_id else 0)
        self.assertEqual(
            self.line_obj.read(self.cursor, self.uid, self.line_ids, fields), before
        )
        self.assertEqual(
            self.move_obj.browse(self.cursor, self.uid, self.move_id).state, "posted"
        )

    def test_wizard_calls_overridable_entry_method_once(self):
        wizard_id = self._wizard()
        with mock.patch.object(
            self.move_obj, "apply_analytic_assignments", return_value=True
        ) as apply_assignments:
            self.wizard_obj.action_apply(
                self.cursor, self.uid, [wizard_id], context=self.context
            )
        self.assertEqual(apply_assignments.call_count, 1)
        self.assertEqual(apply_assignments.call_args[0][2], self.move_id)
        self.assertEqual(
            apply_assignments.call_args[0][3], self._assignments(False)
        )

    def test_rejects_multiple_entries(self):
        with self.assertRaises(osv.except_osv):
            self.wizard_obj.default_get(
                self.cursor, self.uid, ["move_id", "line_ids"],
                context={"active_model": "account.move", "active_ids": [
                    self.move_id, self.move_id,
                ]},
            )

    def test_rejects_unposted_entry(self):
        self.move_obj.write(
            self.cursor, self.uid, [self.move_id], {"state": "draft"}
        )
        with self.assertRaises(osv.except_osv):
            self._wizard()

    def test_rejects_missing_or_foreign_lines(self):
        for assignments in [
            {self.line_ids[0]: self.analytic_id},
            dict(self._assignments(False), **{"99999999": self.analytic_id}),
        ]:
            with self.assertRaises(osv.except_osv):
                self.move_obj.apply_analytic_assignments(
                    self.cursor, self.uid, self.move_id, assignments
                )

    def test_rejects_stale_wizard(self):
        wizard_id = self._wizard()
        self.line_obj.write(
            self.cursor, self.uid, [self.line_ids[0]],
            {"analytic_account_id": self.analytic_id},
        )
        with self.assertRaises(osv.except_osv):
            self.wizard_obj.action_apply(
                self.cursor, self.uid, [wizard_id], context=self.context
            )

    def test_noop_does_not_rebuild_analytic_lines(self):
        self.move_obj.apply_analytic_assignments(
            self.cursor, self.uid, self.move_id, self._assignments(self.analytic_id)
        )
        with mock.patch.object(self.line_obj, "write") as write:
            self.move_obj.apply_analytic_assignments(
                self.cursor, self.uid, self.move_id,
                self._assignments(self.analytic_id),
            )
        self.assertFalse(write.called)

    def test_validates_all_choices_before_writing(self):
        assignments = self._assignments(self.analytic_id)
        assignments[self.line_ids[-1]] = 99999999
        with mock.patch.object(self.line_obj, "write") as write:
            with self.assertRaises(osv.except_osv):
                self.move_obj.apply_analytic_assignments(
                    self.cursor, self.uid, self.move_id, assignments
                )
        self.assertFalse(write.called)

    def test_requires_analytic_journal(self):
        self.openerp.pool.get("account.journal").write(
            self.cursor, self.uid, [self.journal_id],
            {"analytic_journal_id": False},
        )
        with self.assertRaises(osv.except_osv):
            self.move_obj.apply_analytic_assignments(
                self.cursor, self.uid, self.move_id,
                self._assignments(self.analytic_id),
            )

    def test_preserves_real_reconciliation(self):
        self.openerp.pool.get("account.account").write(
            self.cursor, self.uid, [self.account_id], {"reconcile": True}
        )
        self.line_obj.reconcile(self.cursor, self.uid, self.line_ids)
        before = self.line_obj.read(
            self.cursor, self.uid, self.line_ids, ["reconcile_id"]
        )
        self.assertTrue(before[0]["reconcile_id"])
        self.move_obj.apply_analytic_assignments(
            self.cursor, self.uid, self.move_id, self._assignments(self.analytic_id)
        )
        self.assertEqual(
            self.line_obj.read(
                self.cursor, self.uid, self.line_ids, ["reconcile_id"]
            ), before,
        )

    def test_does_not_override_existing_distribution(self):
        journal = self.openerp.pool.get("account.journal").browse(
            self.cursor, self.uid, self.journal_id
        )
        distribution_id = self.openerp.pool.get("account.analytic.distribution").create(
            self.cursor, self.uid, {
                "name": "Existing distribution",
                "journal_id": journal.analytic_journal_id.id,
            },
        )
        self.line_obj.write(
            self.cursor, self.uid, self.line_ids, {"analytics_id": distribution_id}
        )
        with self.assertRaises(osv.except_osv):
            self.move_obj.apply_analytic_assignments(
                self.cursor, self.uid, self.move_id,
                self._assignments(self.analytic_id),
            )

    def test_wizard_view_keeps_accounting_fields_readonly(self):
        view_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "account_analytic_som",
            "view_wizard_reassign_move_analytics",
        )[1]
        view = self.wizard_obj.fields_view_get(
            self.cursor, self.uid, view_id=view_id, view_type="form",
            context=self.context,
        )
        fields = view["fields"]["line_ids"]["views"]["tree"]["fields"]
        for field in ["move_line_id", "account_id", "name", "debit", "credit"]:
            self.assertTrue(fields[field]["readonly"])
        self.assertFalse(fields["analytic_account_id"].get("readonly", False))

    def test_existing_installation_migration_is_repeatable(self):
        path = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "5.0.25.5.0",
            "post-0001_add_analytic_reassignment_wizard.py",
        )
        namespace = {"__name__": "analytic_reassignment_migration"}
        with open(path, "rb") as script:
            exec_(compile(script.read(), path, "exec"), namespace)
        migrate = namespace["up"]
        data_obj = self.openerp.pool.get("ir.model.data")
        with mock.patch.dict(config.options, {"update": {}}):
            for attempt in range(2):
                migrate(self.cursor, "0-dev")
        for xml_id, model in [
            ("view_wizard_reassign_move_analytics", "ir.ui.view"),
            ("value_wizard_reassign_move_analytics", "ir.values"),
            ("access_wizard_reassign_move_analytics", "ir.model.access"),
        ]:
            record_model, record_id = data_obj.get_object_reference(
                self.cursor, self.uid, "account_analytic_som", xml_id
            )
            self.assertEqual(record_model, model)
            self.assertTrue(self.openerp.pool.get(model).search(
                self.cursor, self.uid, [("id", "=", record_id)]
            ))

    def test_rejects_duplicate_items_in_wizard(self):
        wizard_id = self._wizard()
        wizard = self.wizard_obj.browse(self.cursor, self.uid, wizard_id)
        self.openerp.pool.get("wizard.reassign.move.analytics.line").write(
            self.cursor, self.uid, [wizard.line_ids[-1].id],
            {"move_line_id": wizard.line_ids[0].move_line_id.id},
        )
        with self.assertRaises(osv.except_osv):
            self.wizard_obj.action_apply(
                self.cursor, self.uid, [wizard_id], context=self.context
            )

    def test_blank_replaces_explicit_account_with_default(self):
        self.move_obj.apply_analytic_assignments(
            self.cursor, self.uid, self.move_id,
            self._assignments(self.other_analytic_id),
        )
        self._default()
        wizard_id = self._wizard()
        wizard = self.wizard_obj.browse(self.cursor, self.uid, wizard_id)
        self.openerp.pool.get("wizard.reassign.move.analytics.line").write(
            self.cursor, self.uid, [line.id for line in wizard.line_ids],
            {"analytic_account_id": False},
        )
        self.wizard_obj.action_apply(
            self.cursor, self.uid, [wizard_id], context=self.context
        )
        for line in self.line_obj.browse(self.cursor, self.uid, self.line_ids):
            self.assertEqual(line.analytic_account_id.id, self.analytic_id)

    def test_supports_legacy_single_record_action_context(self):
        values = self.wizard_obj.default_get(
            self.cursor, self.uid, ["move_id", "line_ids"],
            context={"active_id": self.move_id},
        )
        self.assertEqual(values["move_id"], self.move_id)
        self.assertEqual(len(values["line_ids"]), len(self.line_ids))

    def test_rejects_action_from_another_model(self):
        with self.assertRaises(osv.except_osv):
            self.wizard_obj.default_get(
                self.cursor, self.uid, ["move_id", "line_ids"],
                context={"active_model": "account.invoice", "active_ids": [self.move_id]},
            )
