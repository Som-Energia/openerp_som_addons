# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction


class TestWizardAccountBalance(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.maxDiff = None

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
        context = {"lang": False, "active_ids": [menu_id], "tz": False, "active_id": menu_id}
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
                    "account_list": [[6, 0, account_list]],
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
