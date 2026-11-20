# -*- coding: utf-8 -*-

from __future__ import absolute_import

import xml.etree.ElementTree as ET

from destral import testing
from tools.misc import cache


class TestAccountInvoiceSom(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.ai_obj = self.openerp.pool.get("account.invoice")
        super(TestAccountInvoiceSom, self).setUp()
        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("origin", "=", False)], limit=2)
        self.ai_obj.write(self.cursor, self.uid, ai_ids[0], {"origin": "sample_origin1"})
        self.ai_obj.write(self.cursor, self.uid, ai_ids[1], {"origin": "sample_origin2"})

    def set_account_invoice_number_cerca_exacte(self, cursor, uid, value):
        res_obj = self.openerp.pool.get("res.config")
        cache.clean_caches_for_db(cursor.dbname)
        res_obj.set(cursor, uid, "account_invoice_number_cerca_exacte", value)

    def test_search_withPercentage_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "1")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("number", "ilike", "FE%")])

        self.assertGreater(len(ai_ids), 1)

    def test_search_exactExist_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "1")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("number", "ilike", "FE210001")])

        self.assertEqual(len(ai_ids), 1)

    def test_search_exactNotExist_active(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "1")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("number", "ilike", "FE")])

        self.assertEqual(len(ai_ids), 0)

    def test_search_withPercentage_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "0")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("number", "ilike", "FE%")])

        self.assertGreater(len(ai_ids), 1)

    def test_search_exactExist_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "0")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("number", "ilike", "FE210001")])

        self.assertEqual(len(ai_ids), 1)

    def test_search_exactNotExist_disabled(self):
        self.set_account_invoice_number_cerca_exacte(self.cursor, self.uid, "0")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("number", "ilike", "FE")])

        self.assertGreater(len(ai_ids), 1)

    def set_invoice_origin_cerca_exacte(self, cursor, uid, value):
        res_obj = self.openerp.pool.get("res.config")
        cache.clean_caches_for_db(cursor.dbname)
        res_obj.set(cursor, uid, "invoice_origin_cerca_exacte", value)

    def test_search_withPercentage_active(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin%")])
        self.assertGreater(len(ai_ids), 1)

    def test_search_exactExist_active(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin1")])

        self.assertEqual(len(ai_ids), 1)

    def test_search_exactNotExist_active(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "1")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin")])

        self.assertEqual(len(ai_ids), 0)

    def test_search_withPercentage_disabled(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin%")])

        self.assertGreater(len(ai_ids), 1)

    def test_search_exactExist_disabled(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin1")])

        self.assertEqual(len(ai_ids), 1)

    def test_search_exactNotExist_disabled(self):  # noqa: F811
        self.set_invoice_origin_cerca_exacte(self.cursor, self.uid, "0")

        ai_ids = self.ai_obj.search(self.cursor, self.uid, [("origin", "ilike", "sample_origin")])

        self.assertGreater(len(ai_ids), 1)


class TestAnalyticAccountDefault(testing.OOTestCaseWithCursor):
    def test_move_line_popup_shows_analytic_account_and_onchange(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        view_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account", "view_move_form"
        )[1]
        move_obj = self.openerp.pool.get("account.move")
        view = move_obj.fields_view_get(
            self.cursor, self.uid, view_id=view_id, view_type="form"
        )

        line_form = ET.fromstring(
            view["fields"]["line_id"]["views"]["form"]["arch"]
        )
        fields = dict((field.get("name"), field) for field in line_form.findall("field"))

        self.assertIn("analytic_account_id", fields)
        self.assertEqual(
            fields["account_id"].get("on_change"),
            "onchange_account_id(account_id, partner_id)",
        )

    def test_account_onchange_returns_analytic_account_field(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        analytic_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account", "analytic_internal"
        )[1]
        default_obj = self.openerp.pool.get("account.analytic.default")
        default_obj.create(
            self.cursor,
            self.uid,
            {"analytic_id": analytic_id, "user_id": self.uid},
        )

        move_line_obj = self.openerp.pool.get("account.move.line")
        result = move_line_obj.onchange_account_id(
            self.cursor, self.uid, [], False, False
        )

        values = result.get("value", {})
        self.assertEqual(values.get("analytic_account_id"), analytic_id)
        self.assertNotIn("account_analytic_id", values)

    def test_partner_onchange_reapplies_analytic_default(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        analytic_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account", "analytic_internal"
        )[1]
        account_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "account", "a_expense"
        )[1]
        partner_obj = self.openerp.pool.get("res.partner")
        partner_id = partner_obj.search(self.cursor, self.uid, [], limit=1)[0]
        default_obj = self.openerp.pool.get("account.analytic.default")
        default_obj.create(
            self.cursor,
            self.uid,
            {
                "analytic_id": analytic_id,
                "user_id": self.uid,
                "account_id": account_id,
                "partner_id": partner_id,
            },
        )

        move_line_obj = self.openerp.pool.get("account.move.line")
        result = move_line_obj.onchange_partner_id(
            self.cursor,
            self.uid,
            [],
            False,
            partner_id,
            account_id,
        )

        self.assertEqual(result["value"].get("analytic_account_id"), analytic_id)
