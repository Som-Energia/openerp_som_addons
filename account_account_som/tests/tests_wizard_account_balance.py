# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
import mock
from osv import fields


class TestWizardAccountBalance(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_get_account_balance_wiz_data_ok(self):
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get("wizard.account.balance.report")
        imd_obj = self.openerp.pool.get("ir.model.data")
        aa_obj = self.openerp.pool.get("account.account")
        account_list = aa_obj.search(cursor, uid, [])
        menu_id = imd_obj.get_object_reference(
            cursor, uid, "account_account_som", "menu_account_balance_full_report_som"
        )[1]
        values = {
            "date_from": "2021-01-01",
            "display_account_level": 0,
            "company_id": 1,
            "state": "none",
            "all_accounts": 1,
            "periods": [(6, 0, [])],
            "date_to": "2021-12-17",
            "account_list": [(6, 0, [])],
            "display_account": "bal_all",
            "fiscalyear": 1,
        }
        context = {
            "lang": False,
            "active_ids": [menu_id],
            "tz": False,
            "active_id": menu_id,
        }
        wiz_id = wiz_obj.create(cursor, uid, values, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        datas = wiz.get_account_balance_wiz_data(context)

        self.assertEqual(
            datas,
            {
                "form": {
                    "date_from": "2021-01-01",
                    "display_account_level": 0,
                    "company_id": 1,
                    "state": "none",
                    "all_accounts": 1,
                    "periods": [(6, 0, [])],
                    "date_to": "2021-12-17",
                    "account_list": [(6, 0, account_list)],
                    "display_account": "bal_all",
                    "fiscalyear": 1,
                    "context": {
                        "lang": False,
                        "active_ids": [menu_id],
                        "tz": False,
                        "active_id": menu_id,
                    },
                }
            },
        )

    @mock.patch("async_reports.async_reports.AsyncReports.waiting_report")
    def test_wizard_account_balance_report_async(self, mock_waiting_report):
        cursor = self.cursor
        uid = self.uid
        wiz_obj = self.openerp.pool.get("wizard.account.balance.report")
        imd_obj = self.openerp.pool.get("ir.model.data")
        aa_obj = self.openerp.pool.get("account.account")
        account_list = aa_obj.search(cursor, uid, [])
        menu_id = imd_obj.get_object_reference(
            cursor, uid, "account_account_som", "menu_account_balance_full_report_som"
        )[1]
        values = {
            "date_from": "2021-01-01",
            "display_account_level": 0,
            "company_id": 1,
            "state": "none",
            "all_accounts": True,
            "periods": [(6, 0, [])],
            "date_to": "2021-12-17",
            "account_list": [(6, 0, [])],
            "display_account": "bal_all",
            "fiscalyear": 1,
        }
        context = {
            "lang": False,
            "active_ids": [menu_id],
            "tz": False,
            "active_id": menu_id,
        }
        wiz_id = wiz_obj.create(cursor, uid, values, context)
        wiz = wiz_obj.browse(cursor, uid, wiz_id)

        result = wiz._report_async(context)

        expected_datas = {
            "form": {
                "date_from": "2021-01-01",
                "display_account_level": 0,
                "company_id": 1,
                "state": "none",
                "all_accounts": True,
                "periods": [(6, 0, [])],
                "date_to": "2021-12-17",
                "account_list": [[6, 0, account_list]],
                "display_account": "bal_all",
                "fiscalyear": 1,
                "context": {
                    "lang": False,
                    "active_ids": [menu_id],
                    "tz": False,
                    "active_id": menu_id,
                },
            },
            "email_to": "fabien@pinckaers.com",
            "from": 1,
        }
        mock_waiting_report.assert_called_with(
            mock.ANY, mock.ANY, [wiz_id], "account.balance.full", expected_datas, context
        )

        self.assertTrue(result)
