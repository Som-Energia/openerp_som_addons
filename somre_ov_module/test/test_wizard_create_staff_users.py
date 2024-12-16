# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from osv.osv import except_osv

from destral import testing
from destral.transaction import Transaction


class WizardCreateStaffUsersTests(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.res_users = self.pool.get('res.users')
        self.res_partner = self.pool.get('res.partner')
        self.res_partner_address = self.pool.get('res.partner.address')
        self.wiz_o = self.pool.get('wizard.create.staff.users')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test__action_create_staff_users__OK(self):
        user_id = self.res_users.search(
            self.cursor,
            self.uid,
            [('login', '=', 'lamaali')]
        )[0]
        irrelevant_context = {}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=irrelevant_context)
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {
            "user_to_staff": user_id,
            "email": 'an_email',
            "vat": 'ES16232335Q'
        }, irrelevant_context)

        self.wiz_o.action_create_staff_users(
            self.cursor, self.uid, [wiz_id], context=irrelevant_context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]
        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], 'Usuaria staff creada')

    def test__action_create_staff_users__res_user_is_already_staff(self):
        user_id = self.res_users.search(
            self.cursor,
            self.uid,
            [('login', '=', 'matahari')]
        )[0]
        irrelevant_context = {}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=irrelevant_context)
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {
            "user_to_staff": user_id,
            "email": 'an_email',
            "vat": 'a_vat_number'
        }, irrelevant_context)

        self.wiz_o.action_create_staff_users(
            self.cursor, self.uid, [wiz_id], context=irrelevant_context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]
        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], 'Aquesta usuaria ja és staff')

    def test__action_create_staff_users__res_user_does_not_exists(self):
        a_non_existing_user_id = 999999999
        irrelevant_context = {}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=irrelevant_context)
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {
            "user_to_staff": a_non_existing_user_id,
            "email": 'an_email',
            "vat": 'a_vat_number'
        }, irrelevant_context)

        self.wiz_o.action_create_staff_users(
            self.cursor, self.uid, [wiz_id], context=irrelevant_context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]
        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], 'No s\'ha trobat cap usuaria')

    def test__action_create_staff_users__with_wrong_vat(self):
        user_id = self.res_users.search(
            self.cursor,
            self.uid,
            [('login', '=', 'lamaali')]
        )[0]
        irrelevant_context = {}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=irrelevant_context)
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {
            "user_to_staff": user_id,
            "email": 'an_email',
            "vat": 'a_wrong_vat_number'
        }, irrelevant_context)

        with self.assertRaises(except_osv) as ctx:
            self.wiz_o.action_create_staff_users(
                self.cursor, self.uid, [wiz_id], context=irrelevant_context)
        self.assertEqual(ctx.exception.name, 'Error validant el VAT!')
