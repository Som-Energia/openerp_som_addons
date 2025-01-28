# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from destral import testing
from destral.transaction import Transaction


class WizardCreateSomreOvUsers(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.imd = self.pool.get('ir.model.data')
        self.rp = self.pool.get('res.partner')
        self.rpa = self.pool.get('res.partner.address')
        self.ov_user = self.pool.get('somre.ov.users')
        self.wiz_o = self.pool.get('wizard.create.somre.ov.users')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def reference(self, module, id):
        return self.imd.get_object_reference(
            self.cursor, self.uid, module, id,
        )[1]

    def test__action_create_somre_ov_users__create_one_ok(self):
        partner_id = self.reference('base', 'res_partner_asus')
        rp = self.rp.browse(self.cursor, self.uid, partner_id)
        self.rpa.write(self.cursor, self.uid, [rp.address[0].id], {
            'email': 'a@a.net',
        })

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 0)

        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context={})
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {'partner_id': partner_id})
        self.wiz_o.action_create_somre_ov_users(self.cursor, self.uid, [wiz_id], context={})

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(
            wiz['info'], u'Usuari de la oficina virtual de representació creat correctament')

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 1)

    def test__action_create_somre_ov_users__already_ov_user_error(self):
        ov_user_id = self.reference('somre_ov_module', 'somre_ov_user_soci')
        partner_id = self.ov_user.read(self.cursor, self.uid, ov_user_id, [
                                       'partner_id'])['partner_id'][0]

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 1)

        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context={})
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {'partner_id': partner_id})
        self.wiz_o.action_create_somre_ov_users(self.cursor, self.uid, [wiz_id], context={})

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(
            wiz['info'], u'El Client ja és usuari de la oficina virtual de representació!')

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 1)

    def test__action_create_somre_ov_users__same_vat_error(self):
        partner_id = self.reference('base', 'res_partner_asus')

        ov_user_id = self.reference('somre_ov_module', 'somre_ov_user_soci')
        ov_u = self.ov_user.browse(self.cursor, self.uid, ov_user_id)
        VAT = ov_u.vat

        somre_ov_user_partner_ids = self.rp.search(self.cursor, self.uid, [
            ('vat', '=', VAT)
        ])
        self.assertEqual(len(somre_ov_user_partner_ids), 1)
        self.rp.write(self.cursor, self.uid, [partner_id], {
            'vat': VAT
        })
        result = self.rp.search(self.cursor, self.uid, [
            ('vat', '=', VAT)
        ])
        self.assertEqual(len(result), 2)

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 0)

        result = self.ov_user.search(self.cursor, self.uid, [(
            'partner_id', '=', somre_ov_user_partner_ids[0])])
        self.assertEqual(len(result), 1)

        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context={})
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {'partner_id': partner_id})
        self.wiz_o.action_create_somre_ov_users(self.cursor, self.uid, [wiz_id], context={})

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], u'Ja existeix un usuari amb aquest NIF!')

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 0)

    def test__action_create_somre_ov_users__no_email_error(self):
        partner_id = self.reference('base', 'res_partner_asus')
        rp = self.rp.browse(self.cursor, self.uid, partner_id)
        self.rpa.write(self.cursor, self.uid, [rp.address[0].id], {
            'email': False,
        })

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 0)

        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context={})
        self.wiz_o.write(self.cursor, self.uid, [wiz_id], {'partner_id': partner_id})
        self.wiz_o.action_create_somre_ov_users(self.cursor, self.uid, [wiz_id], context={})

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], u'El Client no té correu electrónic definit')

        result = self.ov_user.search(self.cursor, self.uid, [('partner_id', '=', partner_id)])
        self.assertEqual(len(result), 0)
