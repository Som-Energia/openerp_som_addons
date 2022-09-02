# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from expects import *
from datetime import datetime,date
from random import choice

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

    def search_in(self, model, params, who=0):
        model_obj = self.get_model(model)
        found_ids = model_obj.search(self.cursor, self.uid, params)
        if not found_ids:
            return None
        if who == 'random':
            return choice(found_ids)
        return found_ids[who]

    def browse_referenced(self, reference):
        model, id = reference.split(',')
        model_obj = self.get_model(model)
        return model_obj.browse(self.cursor, self.uid, int(id))



class CallInfoCallLogTest(CallInfoBaseTests):

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

    def test_insert_call_log__basic(self):
        cil_obj = self.get_model('call.info.call.log')

        call_data = {
            'user_id': self.search_in('res.users',[]),
            'categ_id': self.search_in('call.info.call.category',[]),
            'notes': 'bla bla bla, complex explanation, ...',
        }

        call_id = cil_obj.insert_call_log(self.cursor, self.uid, call_data, {})
        call = cil_obj.browse(self.cursor, self.uid, call_id)

        self.assertEqual(call.comment, call_data['notes'])
        self.assertEqual(call.call_date[:10], today_str())
        self.assertEqual(call.user_id.id, call_data['user_id'])
        self.assertEqual(call.categ_id.id, call_data['categ_id'])
        self.assertEqual(call.phone, False)
        self.assertEqual(call.polissa_id, False)
        self.assertEqual(call.partner_id.id, False)


    def test_insert_call_log__time(self):
        cil_obj = self.get_model('call.info.call.log')

        call_data = {
            'user_id': self.search_in('res.users',[]),
            'categ_id': self.search_in('call.info.call.category',[]),
            'notes': 'bla bla bla, complex explanation, ...',
            'call_date': '2022-08-15 15:31:32',
        }

        call_id = cil_obj.insert_call_log(self.cursor, self.uid, call_data, {})
        call = cil_obj.browse(self.cursor, self.uid, call_id)

        self.assertEqual(call.comment, call_data['notes'])
        self.assertEqual(call.call_date, call_data['call_date'])
        self.assertEqual(call.user_id.id, call_data['user_id'])
        self.assertEqual(call.categ_id.id, call_data['categ_id'])

    def test_insert_call_log__phone(self):
        cil_obj = self.get_model('call.info.call.log')

        call_data = {
            'user_id': self.search_in('res.users',[]),
            'categ_id': self.search_in('call.info.call.category',[],'random'),
            'notes': 'bla bla bla, complex explanation, ...',
            'phone': '0034900103605 som'
        }

        call_id = cil_obj.insert_call_log(self.cursor, self.uid, call_data, {})
        call = cil_obj.browse(self.cursor, self.uid, call_id)

        self.assertEqual(call.comment, call_data['notes'])
        self.assertEqual(call.call_date[:10], today_str())
        self.assertEqual(call.user_id.id, call_data['user_id'])
        self.assertEqual(call.categ_id.id, call_data['categ_id'])
        self.assertEqual(call.phone, '900103605')

    def test_insert_call_log__contract(self):
        cil_obj = self.get_model('call.info.call.log')
        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001')[1]

        call_data = {
            'user_id': self.search_in('res.users',[]),
            'categ_id': self.search_in('call.info.call.category',[],'random'),
            'notes': 'bla bla bla, complex explanation, ...',
            'polissa_id': polissa_id,
        }

        call_id = cil_obj.insert_call_log(self.cursor, self.uid, call_data, {})
        call = cil_obj.browse(self.cursor, self.uid, call_id)

        self.assertEqual(call.comment, call_data['notes'])
        self.assertEqual(call.call_date[:10], today_str())
        self.assertEqual(call.user_id.id, call_data['user_id'])
        self.assertEqual(call.categ_id.id, call_data['categ_id'])
        self.assertEqual(call.contract_id.id, polissa_id)

    def test_insert_call_log__partner(self):
        cil_obj = self.get_model('call.info.call.log')
        ir_obj = self.get_model('ir.model.data')
        partner_id = ir_obj.get_object_reference(self.cursor, self.uid, 'base', 'main_partner')[1]

        call_data = {
            'user_id': self.search_in('res.users',[]),
            'categ_id': self.search_in('call.info.call.category',[],'random'),
            'notes': 'bla bla bla, complex explanation, ...',
            'partner_id': partner_id,
        }

        call_id = cil_obj.insert_call_log(self.cursor, self.uid, call_data, {})
        call = cil_obj.browse(self.cursor, self.uid, call_id)

        self.assertEqual(call.comment, call_data['notes'])
        self.assertEqual(call.call_date[:10], today_str())
        self.assertEqual(call.user_id.id, call_data['user_id'])
        self.assertEqual(call.categ_id.id, call_data['categ_id'])
        self.assertEqual(call.partner_id.id, partner_id)

    def test_insert_call_log__all_identifiers(self):
        cil_obj = self.get_model('call.info.call.log')
        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001')[1]
        partner_id = ir_obj.get_object_reference(self.cursor, self.uid, 'base', 'main_partner')[1]

        call_data = {
            'user_id': self.search_in('res.users',[]),
            'categ_id': self.search_in('call.info.call.category',[],'random'),
            'notes': 'bla bla bla, complex explanation, ...',
            'partner_id': partner_id,
            'polissa_id': polissa_id,
            'phone': '(0034)900.103.605 som'
        }

        call_id = cil_obj.insert_call_log(self.cursor, self.uid, call_data, {})
        call = cil_obj.browse(self.cursor, self.uid, call_id)

        self.assertEqual(call.comment, call_data['notes'])
        self.assertEqual(call.call_date[:10], today_str())
        self.assertEqual(call.user_id.id, call_data['user_id'])
        self.assertEqual(call.categ_id.id, call_data['categ_id'])
        self.assertEqual(call.partner_id.id, partner_id)
        self.assertEqual(call.phone, '900103605')
        self.assertEqual(call.contract_id.id, polissa_id)
