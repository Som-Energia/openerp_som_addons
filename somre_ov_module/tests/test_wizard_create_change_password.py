# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from destral import testing
from destral.transaction import Transaction
from ..models.exceptions import FailSendEmail
from ..wizard.wizard_create_change_password import WizardCreateChangePassword

import mock


class WizardCreateChangePasswordTests(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.res_partner = self.pool.get('res.partner')
        self.wiz_o = self.pool.get('wizard.create.change.password')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__OK(self, mock_save_privisioning_data):
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        context = {'active_ids': partner_id}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], 'Contrasenyes generades')

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__KO_cannot_save_privisioning_data(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        context = {'active_ids': partner_id}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = False

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {} ({})\n'.format(
            'Error generant contrasenyes pels següents partners',
            int(partner_id[0]),
            'Error al guardar la contrasenya'
        )
        )
        mock_send_password_email.assert_not_called()

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__KO_cannot_send_password_email(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        context = {'active_ids': partner_id}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        def send_password_email(cursor, uid, partner_id):
            raise FailSendEmail('Error text')

        mock_send_password_email.side_effect = send_password_email

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {} ({})\n'.format(
            'Error generant contrasenyes pels següents partners',
            int(partner_id[0]),
            "Error al generar/enviar l'email")
        )

    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__multiple_partners__OK(self, mock_save_privisioning_data):  # noqa: E501
        partner_ids = self.res_partner.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': partner_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], 'Contrasenyes generades')

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__multiple_partners__KO_cannot_save_privisioning_data(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        partner_ids = self.res_partner.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': partner_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = False

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {}'.format(
            'Error generant contrasenyes pels següents partners',
            ','.join(['{} ({})\n'.format(str(int(x)), 'Error al guardar la contrasenya')
                     for x in partner_ids])
        )
        )

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__multiple_partners__KO_cannot_save_privisioning_data__even_partner_id(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        partner_ids = self.res_partner.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': partner_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        def save_privisioning_data(cursor, uid, partner_id, password):
            if partner_id % 2 == 0:
                return False
            return True

        mock_save_privisioning_data.side_effect = save_privisioning_data

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {}'.format(
            'Error generant contrasenyes pels següents partners',
            ','.join(['{} ({})\n'.format(str(int(x)), 'Error al guardar la contrasenya')
                     for x in partner_ids if x % 2 == 0])
        )
        )

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__KO_cannot_send_password_email__even_partner_id(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        partner_ids = self.res_partner.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': partner_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        def send_password_email(cursor, uid, partner_id):
            if int(partner_id.id) % 2 == 0:
                raise FailSendEmail('Error text')

        mock_send_password_email.side_effect = send_password_email

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {}'.format(
            'Error generant contrasenyes pels següents partners',
            ','.join(['{} ({})\n'.format(str(int(x)), "Error al generar/enviar l'email")
                     for x in partner_ids if x % 2 == 0])
        )
        )

    @mock.patch("tools.config.get")
    def test__save_privisioning_data__KO_without_api_key(self, mock_config):
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        password = 'test-password'

        mock_config.return_value = False

        result = self.wiz_o.save_privisioning_data(self.cursor, self.uid, partner_id[0], password)

        self.assertFalse(result)

    def test__add_password_to_partner_comment__comment_empty(self):
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        password = 'test-password'

        self.wiz_o.add_password_to_partner_comment(self.cursor, self.uid, partner_id[0], password)

        partner = self.res_partner.browse(self.cursor, self.uid, partner_id[0])

        self.assertTrue('generated_ov_password' in partner.comment)

    def test__add_password_to_partner_comment__comment_not_empty(self):
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        password = 'test-password'
        self.res_partner.write(self.cursor, self.uid, partner_id[0], {'comment': 'one_comment'})

        self.wiz_o.add_password_to_partner_comment(self.cursor, self.uid, partner_id[0], password)

        partner = self.res_partner.browse(self.cursor, self.uid, partner_id[0])

        self.assertTrue('generated_ov_password' in partner.comment)

    def test__add_password_to_partner_comment__comment_has_generated_password(self):
        partner_id = self.res_partner.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        password = 'new_test_password'
        comment = 'one_comment\ngenerated_ov_password=test_password(generated_ov_password)\n'
        self.res_partner.write(self.cursor, self.uid, partner_id[0], {'comment': comment})

        self.wiz_o.add_password_to_partner_comment(self.cursor, self.uid, partner_id[0], password)

        partner = self.res_partner.browse(self.cursor, self.uid, partner_id[0])

        self.assertTrue('new_test_password' in partner.comment)
