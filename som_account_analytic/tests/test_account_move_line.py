# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from lxml import etree
import mock


class TestManualEntryAnalytics(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestManualEntryAnalytics, self).setUp()
        self.line_obj = self.openerp.pool.get("account.move.line")
        self.default_obj = self.openerp.pool.get("account.analytic.default")
        account_obj = self.openerp.pool.get("account.account")
        self.account_id = account_obj.search(
            self.cursor, self.uid, [("type", "!=", "view")], limit=1
        )[0]
        account = account_obj.browse(self.cursor, self.uid, self.account_id)
        self.expected_tax_id = account.tax_ids and account.tax_ids[0].id or False

    def test_matching_default_populates_move_line_field(self):
        rule_ids = self.default_obj.search(self.cursor, self.uid, [])
        self.default_obj.unlink(self.cursor, self.uid, rule_ids)
        analytic_obj = self.openerp.pool.get("account.analytic.account")
        analytic_id = analytic_obj.create(
            self.cursor, self.uid, {"name": "Manual entry test"}
        )
        self.default_obj.create(
            self.cursor, self.uid,
            {"account_id": self.account_id, "analytic_id": analytic_id},
        )

        result = self.line_obj.onchange_account_id(
            self.cursor, self.uid, [], self.account_id, False
        )

        self.assertEqual(result["value"]["analytic_account_id"], analytic_id)
        self.assertNotIn("account_analytic_id", result["value"])
        self.assertEqual(result["value"]["account_tax_id"], self.expected_tax_id)

    def test_no_default_preserves_inherited_values(self):
        with mock.patch.object(self.default_obj, "account_get", return_value=False):
            result = self.line_obj.onchange_account_id(
                self.cursor, self.uid, [], self.account_id, False
            )

        self.assertEqual(result["value"]["account_tax_id"], self.expected_tax_id)
        self.assertNotIn("analytic_account_id", result["value"])
        self.assertNotIn("account_analytic_id", result["value"])

    def test_distribution_value_is_preserved(self):
        rule = mock.Mock()
        rule.analytic_id.id = 42
        rule.analytics_id.id = 37
        with mock.patch.object(self.default_obj, "account_get", return_value=rule):
            result = self.line_obj.onchange_account_id(
                self.cursor, self.uid, [], self.account_id, False
            )

        self.assertEqual(result["value"]["analytic_account_id"], 42)
        self.assertEqual(result["value"]["analytics_id"], 37)
        self.assertEqual(result["value"]["account_tax_id"], self.expected_tax_id)

    def test_empty_account_without_default(self):
        with mock.patch.object(self.default_obj, "account_get", return_value=False):
            result = self.line_obj.onchange_account_id(
                self.cursor, self.uid, [], False, False
            )

        self.assertEqual(result, {"value": {}})

    def test_effective_view_preserves_popup_and_tree_fields(self):
        data_obj = self.openerp.pool.get("ir.model.data")
        view_id = data_obj.get_object_reference(
            self.cursor, self.uid, "account", "view_move_form"
        )[1]
        move_obj = self.openerp.pool.get("account.move")
        result = move_obj.fields_view_get(
            self.cursor, self.uid, view_id=view_id, view_type="form"
        )
        line_views = result["fields"]["line_id"]["views"]
        popup = etree.fromstring(line_views["form"]["arch"])
        tree = etree.fromstring(line_views["tree"]["arch"])

        self.assertEqual(len(popup.xpath("field[@name='analytic_account_id']")), 1)
        self.assertEqual(
            popup.xpath("field[@name='account_id']")[0].get("on_change"),
            "onchange_account_id(account_id, partner_id)",
        )
        self.assertEqual(len(tree.xpath("field[@name='analytic_account_id']")), 1)
        self.assertEqual(len(tree.xpath("field[@name='analytics_id']")), 1)
