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

    def test_normalize_phone_ok(self):
        cil_obj = self.get_model('call.info.call.log')

        phone_clean = cil_obj._normalize_phone_number('872.202.550')
        self.assertEqual(phone_clean, '872202550')

        phone_clean = cil_obj._normalize_phone_number('900.103.605')
        self.assertEqual(phone_clean, '900103605')

    def test_normalize_phone_various(self):
        cil_obj = self.get_model('call.info.call.log')

        samples = [
            {'raw': '123456789', 'clean': '123456789'},
            {'raw': '123.456.789', 'clean': '123456789'},
            {'raw': '123.45.67.89', 'clean': '123456789'},
            {'raw': '123-456-789', 'clean': '123456789'},
            {'raw': '123-45-67-89', 'clean': '123456789'},
            {'raw': '(+34)123456789', 'clean': '123456789'},
            {'raw': '0034 123-456.789', 'clean': '123456789'},
            {'raw': '(+49)123456789', 'clean': '49123456789'},
            {'raw': '0049 123-456.789', 'clean': '49123456789'},
            {'raw': ' 123456789  ', 'clean': '123456789'},
            {'raw': '000  00123456789', 'clean': '123456789'},
            {'raw': '00000000000', 'clean': ''},
            {'raw': '123 45.6.78-9 someone', 'clean': '123456789'},
        ]
        for sample in samples:
            result = cil_obj._normalize_phone_number(sample['raw'])
            self.assertEqual(result, sample['clean'])
