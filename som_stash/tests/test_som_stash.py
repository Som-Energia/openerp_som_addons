# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import datetime


def get_minutes(then_str, now):
    difference = datetime.strptime(then_str, "%Y-%m-%d %H:%M:%S") - now
    return difference.total_seconds() / 60.0


def get_data_for_id(results, r_id):
    for result in results:
        if result['id'] == r_id:
            return result
    return None


class SomStashBaseTests(testing.OOTestCase):
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
        model, id = reference.split(",")
        model_obj = self.get_model(model)
        return model_obj.browse(self.cursor, self.uid, int(id))

    def get_object_reference(self, module, semantic_id):
        ir_obj = self.get_model("ir.model.data")
        expected_id = ir_obj.get_object_reference(
            self.cursor, self.uid, module, semantic_id
        )
        return expected_id


class SomStashSettingsTests(SomStashBaseTests):
    def create_setting(self, model, field, value):
        set_obj = self.get_model('som.stash.setting')
        irm_obj = self.get_model('ir.model')
        irf_obj = self.get_model('ir.model.fields')

        irm_ids = irm_obj.search(self.cursor, self.uid, [
            ('model', '=', model),
        ])
        irf_ids = irf_obj.search(self.cursor, self.uid, [
            ('model', '=', model),
            ('name', '=', field),
        ])

        if len(irm_ids) != 1 or len(irf_ids) != 1:
            return None

        vars = {
            'model': irm_ids[0],
            'field': irf_ids[0],
            'default_stashed_value': value
        }
        return set_obj.create(self.cursor, self.uid, vars)

    def create_settings(self, model, f_values):
        res = []
        for k, v in f_values.items():
            res.append(self.create_setting(model, k, v))

        return res

    def create_settings_for_address(self):
        address_fields = {
            'email': 'a@a.com',
            'phone': '999999999',
            'mobile': '666666666',
            'fax': '777777777',
            'street': 'Rue del Percebe, 13',
        }
        return self.create_settings('res.partner.address', address_fields)

    def create_settings_for_partner(self):
        address_fields = {
            'name': 'ningú',
            'ref': 'S000XXXX',
        }
        return self.create_settings('res.partner', address_fields)

    def create_settings_for_test(self):
        a = self.create_settings_for_address()
        b = self.create_settings_for_partner()
        return a + b


class SomStashTest(SomStashSettingsTests):

    def get_stashed_values(self, model, item_id, field):
        stash_obj = self.get_model('som.stash')

        stashed_fields_ids = stash_obj.search(self.cursor, self.uid, [
            ('origin', '=', '{},{}'.format(model, item_id)),
            ('res_model', '=', model),
            ('res_id', '=', item_id),
            ('res_field', '=', field),
        ])

        return stash_obj.read(self.cursor, self.uid, stashed_fields_ids, [
            'value',
            'date_stashed',
        ])

    def test_do_stash__res_partner__one_case_full(self):
        # explain: this partner has name and ref --> 2 values to stash
        rp_obj = self.get_model('res.partner')
        stash_obj = self.get_model('som.stash')

        self.create_settings_for_partner()

        id_1 = self.get_object_reference('base', 'res_partner_asus')[1]

        data_pre = rp_obj.read(self.cursor, self.uid, id_1, ['name', 'ref'])

        todayhm = datetime.today()

        n_stash_items = len(stash_obj.search(self.cursor, self.uid, []))
        result = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        n_stash_items = len(stash_obj.search(self.cursor, self.uid, [])) - n_stash_items

        data_post = rp_obj.read(self.cursor, self.uid, id_1, ['name', 'ref'])

        # test that the values are overwritten with defaults if original values exists
        self.assertEqual('ningú', data_post['name'])
        self.assertEqual('S000XXXX', data_post['ref'])
        self.assertEqual(id_1, data_post['id'])

        # test that the values are stored in stash registers if original values exists
        for k in ['name', 'ref']:
            values = self.get_stashed_values('res.partner', id_1, k)
            self.assertEqual(len(values), 1)
            self.assertEqual(values[0]['value'], data_pre[k])
            self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], id_1)

        # test that right number of registers where created
        self.assertEqual(n_stash_items, 2)

    def test_do_stash__res_partner__one_case_half(self):
        # explain: this partner has name but has no ref (false) --> 1 value to stash
        rp_obj = self.get_model('res.partner')
        stash_obj = self.get_model('som.stash')

        self.create_settings_for_partner()

        id_3 = self.get_object_reference('base', 'res_partner_maxtor')[1]

        data_pre = rp_obj.read(self.cursor, self.uid, id_3, ['name', 'ref'])

        todayhm = datetime.today()

        n_stash_items = len(stash_obj.search(self.cursor, self.uid, []))
        result = stash_obj.do_stash(self.cursor, self.uid, [id_3], 'res.partner')
        n_stash_items = len(stash_obj.search(self.cursor, self.uid, [])) - n_stash_items

        data_post = rp_obj.read(self.cursor, self.uid, id_3, ['name', 'ref'])

        # test that the values are overwritten with defaults if original values exists
        self.assertEqual('ningú', data_post['name'])
        self.assertEqual(False, data_post['ref'])
        self.assertEqual(id_3, data_post['id'])

        # test that the values are stored in stash registers if original values exists
        values = self.get_stashed_values('res.partner', id_3, 'name')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['value'], data_pre['name'])
        self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)
        values = self.get_stashed_values('res.partner', id_3, 'ref')
        self.assertEqual(len(values), 0)

        # test that all where modified
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], id_3)

        # test that right number of registers where created
        self.assertEqual(n_stash_items, 1)

    def test_do_stash__res_partner__some_case(self):
        rp_obj = self.get_model('res.partner')
        stash_obj = self.get_model("som.stash")

        self.create_settings_for_test()

        id_1 = self.get_object_reference('base', 'res_partner_asus')[1]
        id_2 = self.get_object_reference('base', 'res_partner_agrolait')[1]
        id_3 = self.get_object_reference('base', 'res_partner_maxtor')[1]
        id_4 = self.get_object_reference('base', 'res_partner_desertic_hispafuentes')[1]
        ids = [id_1, id_2, id_3, id_4]

        data_pre = rp_obj.read(self.cursor, self.uid, ids, ['name', 'ref'])

        todayhm = datetime.today()

        n_stash_items = len(stash_obj.search(self.cursor, self.uid, []))
        result = stash_obj.do_stash(self.cursor, self.uid, ids, 'res.partner')
        n_stash_items = len(stash_obj.search(self.cursor, self.uid, [])) - n_stash_items

        data_post = rp_obj.read(self.cursor, self.uid, ids, ['name', 'ref'])

        # test that the values are overwritten with defaults if original values exists
        self.assertEqual('ningú', data_post[0]['name'])
        self.assertEqual('S000XXXX', data_post[0]['ref'])
        self.assertEqual(id_1, data_post[0]['id'])
        self.assertEqual('ningú', data_post[1]['name'])
        self.assertEqual('S000XXXX', data_post[1]['ref'])
        self.assertEqual(id_2, data_post[1]['id'])
        self.assertEqual('ningú', data_post[2]['name'])
        self.assertEqual(False, data_post[2]['ref'])
        self.assertEqual(id_3, data_post[2]['id'])
        self.assertEqual('ningú', data_post[3]['name'])
        self.assertEqual(False, data_post[3]['ref'])
        self.assertEqual(id_4, data_post[3]['id'])

        # test that the values are stored in stash registers if original values exists
        data_pre_v = get_data_for_id(data_pre, id_1)
        self.assertEqual(id_1, data_pre_v['id'])
        values = self.get_stashed_values('res.partner', id_1, 'name')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['value'], data_pre_v['name'])
        self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)
        values = self.get_stashed_values('res.partner', id_1, 'ref')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['value'], data_pre_v['ref'])
        self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)

        data_pre_v = get_data_for_id(data_pre, id_2)
        self.assertEqual(id_2, data_pre_v['id'])
        values = self.get_stashed_values('res.partner', id_2, 'name')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['value'], data_pre_v['name'])
        self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)
        values = self.get_stashed_values('res.partner', id_2, 'ref')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['value'], data_pre_v['ref'])
        self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)

        data_pre_v = get_data_for_id(data_pre, id_3)
        self.assertEqual(id_3, data_pre_v['id'])
        values = self.get_stashed_values('res.partner', id_3, 'name')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['value'], data_pre_v['name'])
        self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)
        values = self.get_stashed_values('res.partner', id_3, 'ref')
        self.assertEqual(len(values), 0)

        data_pre_v = get_data_for_id(data_pre, id_4)
        self.assertEqual(id_4, data_pre_v['id'])
        values = self.get_stashed_values('res.partner', id_4, 'name')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]['value'], data_pre_v['name'])
        self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)
        values = self.get_stashed_values('res.partner', id_4, 'ref')
        self.assertEqual(len(values), 0)

        # test that the values are stored in stash registers
        # same but iterative
        for c, id in enumerate(ids):
            data_pre_v = get_data_for_id(data_pre, id)
            for k in ['name', 'ref']:
                values = self.get_stashed_values('res.partner', id, k)
                if k in data_pre_v and data_pre_v[k]:
                    self.assertEqual(len(values), 1)
                    self.assertEqual(values[0]['value'], data_pre_v[k])
                    self.assertLessEqual(
                        get_minutes(values[0]['date_stashed'], todayhm), 5)
                else:
                    self.assertEqual(len(values), 0)

        # test that all where modified
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], id_1)
        self.assertEqual(result[1], id_2)
        self.assertEqual(result[2], id_3)
        self.assertEqual(result[3], id_4)

        # test that right number of registers where created
        self.assertEqual(n_stash_items, 2 + 2 + 1 + 1)

    def test_do_stash__res_partner__one_case_twice(self):
        rp_obj = self.get_model('res.partner')
        stash_obj = self.get_model('som.stash')

        self.create_settings_for_partner()

        id_1 = self.get_object_reference('base', 'res_partner_asus')[1]

        data_pre = rp_obj.read(self.cursor, self.uid, id_1, ['name', 'ref'])

        todayhm = datetime.today()

        n_stash_items = len(stash_obj.search(self.cursor, self.uid, []))
        result_1 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        result_2 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        n_stash_items = len(stash_obj.search(self.cursor, self.uid, [])) - n_stash_items

        data_post = rp_obj.read(self.cursor, self.uid, id_1, ['name', 'ref'])

        # test that the values are overwritten with defaults if original values exists
        self.assertEqual('ningú', data_post['name'])
        self.assertEqual('S000XXXX', data_post['ref'])
        self.assertEqual(id_1, data_post['id'])

        # test that the values are stored in stash registers
        for k in ['name', 'ref']:
            values = self.get_stashed_values('res.partner', id_1, k)
            self.assertEqual(len(values), 1)
            self.assertEqual(values[0]['value'], data_pre[k])
            self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)

        # test that all where modified only first time
        self.assertEqual(len(result_1), 1)
        self.assertEqual(result_1[0], id_1)
        self.assertEqual(len(result_2), 0)

        # test that right number of registers where created
        self.assertEqual(n_stash_items, 2)

    def test_do_stash__res_partner__one_case_more(self):
        rp_obj = self.get_model('res.partner')
        stash_obj = self.get_model('som.stash')

        self.create_settings_for_partner()

        id_1 = self.get_object_reference('base', 'res_partner_asus')[1]

        data_pre = rp_obj.read(self.cursor, self.uid, id_1, ['name', 'ref'])

        todayhm = datetime.today()

        n_stash_items = len(stash_obj.search(self.cursor, self.uid, []))
        result_1 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        result_2 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        result_2 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        result_2 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        result_2 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        result_2 = stash_obj.do_stash(self.cursor, self.uid, [id_1], 'res.partner')
        n_stash_items = len(stash_obj.search(self.cursor, self.uid, [])) - n_stash_items

        data_post = rp_obj.read(self.cursor, self.uid, id_1, ['name', 'ref'])

        # test that the values are overwritten with defaults if original values exists
        self.assertEqual('ningú', data_post['name'])
        self.assertEqual('S000XXXX', data_post['ref'])
        self.assertEqual(id_1, data_post['id'])

        # test that the values are stored in stash registers
        for k in ['name', 'ref']:
            values = self.get_stashed_values('res.partner', id_1, k)
            self.assertEqual(len(values), 1)
            self.assertEqual(values[0]['value'], data_pre[k])
            self.assertLessEqual(get_minutes(values[0]['date_stashed'], todayhm), 5)

        # test that all where modified only first time
        self.assertEqual(len(result_1), 1)
        self.assertEqual(result_1[0], id_1)
        self.assertEqual(len(result_2), 0)

        # test that right number of registers where created
        self.assertEqual(n_stash_items, 2)


class WizardSomStasherTest(SomStashSettingsTests):
    def test_get_partners_origin_to_stash__find_one(self):
        wstahser_obj = self.get_model('wizard.som.stasher')

        date_limit = datetime.datetime(2021,1,1,0,0,0)



        ids = wstahser_obj.get_partners_origin_to_stash(self.cursor, self.uid, datelimit)