# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing


class TestAnalyticDefaultMatching(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestAnalyticDefaultMatching, self).setUp()
        self.default_obj = self.openerp.pool.get("account.analytic.default")
        rule_ids = self.default_obj.search(self.cursor, self.uid, [])
        self.default_obj.unlink(self.cursor, self.uid, rule_ids)
        account_obj = self.openerp.pool.get("account.account")
        self.account_id, self.other_account_id = account_obj.search(
            self.cursor, self.uid, [("type", "!=", "view")], limit=2
        )
        analytic_obj = self.openerp.pool.get("account.analytic.account")
        self.account_analytic_id = analytic_obj.create(
            self.cursor, self.uid, {"name": "Account default"}
        )
        self.product_analytic_id = analytic_obj.create(
            self.cursor, self.uid, {"name": "Product default"}
        )
        data_obj = self.openerp.pool.get("ir.model.data")
        self.product_id = data_obj.get_object_reference(
            self.cursor, self.uid, "product", "product_product_0"
        )[1]
        self.other_product_id = data_obj.get_object_reference(
            self.cursor, self.uid, "product", "product_product_1"
        )[1]
        self.account_rule_id = self.default_obj.create(
            self.cursor, self.uid, {
                "account_id": self.account_id,
                "analytic_id": self.account_analytic_id,
                "sequence": 0,
            }
        )
        self.product_rule_id = self.default_obj.create(
            self.cursor, self.uid, {
                "product_id": self.product_id,
                "analytic_id": self.product_analytic_id,
                "sequence": 3,
            }
        )

    def test_missing_product_keeps_account_default(self):
        rule = self.default_obj.account_get(
            self.cursor, self.uid, account_id=self.account_id, product_id=False
        )

        self.assertEqual(rule.id, self.account_rule_id)
        self.assertEqual(rule.analytic_id.id, self.account_analytic_id)

    def test_missing_product_without_account_default_returns_false(self):
        rule = self.default_obj.account_get(
            self.cursor, self.uid,
            account_id=self.other_account_id, product_id=False
        )

        self.assertFalse(rule)

    def test_matching_product_default_is_preserved(self):
        rule = self.default_obj.account_get(
            self.cursor, self.uid,
            account_id=self.other_account_id, product_id=self.product_id
        )

        self.assertEqual(rule.id, self.product_rule_id)
        self.assertEqual(rule.analytic_id.id, self.product_analytic_id)

    def test_different_product_does_not_match(self):
        rule = self.default_obj.account_get(
            self.cursor, self.uid,
            account_id=self.other_account_id, product_id=self.other_product_id
        )

        self.assertFalse(rule)

    def test_omitted_product_preserves_unrestricted_lookup(self):
        rule = self.default_obj.account_get(
            self.cursor, self.uid, account_id=self.other_account_id
        )

        self.assertEqual(rule.id, self.product_rule_id)

    def test_sequence_still_breaks_equal_score_ties(self):
        generic_rule_id = self.default_obj.create(
            self.cursor, self.uid, {
                "analytic_id": self.product_analytic_id, "sequence": -1,
            }
        )
        rule = self.default_obj.account_get(
            self.cursor, self.uid, account_id=self.account_id, product_id=False
        )

        self.assertEqual(rule.id, generic_rule_id)

    def test_distribution_domain_is_preserved(self):
        domain = self.default_obj.domain_get(
            product_id=False, src_analytic_id=self.account_analytic_id
        )

        self.assertIn(("product_id", "=", False), domain)
        self.assertIn(("src_analytic_id", "=", self.account_analytic_id), domain)
