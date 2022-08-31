# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from expects import *
from datetime import datetime


def today_str():
    return date.today().strftime("%Y-%m-%d")

def today_minus_str(d):
    return (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")


class CallInfoBaseTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def search_in(self, model, params):
        model_obj = self.get_model(model)
        found_ids = model_obj.search(self.cursor, self.uid, params)
        return found_ids[0] if found_ids else None

    def browse_referenced(self, reference):
        model, id = reference.split(',')
        model_obj = self.get_model(model)
        return model_obj.browse(self.cursor, self.uid, int(id))



class CallInfoCallLogTest(CallInfoBaseTests):

    def test_normalize_phone_dummy(self):
        self.assertEqual(1,1)

