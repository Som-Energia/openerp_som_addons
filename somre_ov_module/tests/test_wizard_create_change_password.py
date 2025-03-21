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
        self.ov_user = self.pool.get('somre.ov.users')
        self.wiz_o = self.pool.get('wizard.create.change.password')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__OK(self, mock_save_privisioning_data):
        ov_user_id = self.ov_user.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        context = {'active_ids': ov_user_id}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], 'Contrasenyes generades')

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__KO_cannot_save_privisioning_data(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        ov_user_id = self.ov_user.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        context = {'active_ids': ov_user_id}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = False

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {} ({})\n'.format(
            'Error generant contrasenyes pels següents partners',
            int(ov_user_id[0]),
            'Error al guardar la contrasenya'
        )
        )
        mock_send_password_email.assert_not_called()

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__KO_cannot_send_password_email(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        ov_user_id = self.ov_user.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        context = {'active_ids': ov_user_id}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        def send_password_email(cursor, uid, ov_user_id):
            raise FailSendEmail('Error text')

        mock_send_password_email.side_effect = send_password_email

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {} ({})\n'.format(
            'Error generant contrasenyes pels següents partners',
            int(ov_user_id[0]),
            "Error al generar/enviar l'email")
        )

    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__multiple_partners__OK(self, mock_save_privisioning_data):  # noqa: E501
        ov_user_ids = self.ov_user.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': ov_user_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], 'Contrasenyes generades')

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__multiple_partners__KO_cannot_save_privisioning_data(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        ov_user_ids = self.ov_user.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': ov_user_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = False

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {}'.format(
            'Error generant contrasenyes pels següents partners',
            ','.join(['{} ({})\n'.format(str(int(x)), 'Error al guardar la contrasenya')
                     for x in ov_user_ids])
        )
        )

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__multiple_partners__KO_cannot_save_privisioning_data__even_partner_id(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        ov_user_ids = self.ov_user.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': ov_user_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        def save_privisioning_data(cursor, uid, partner_id, password):
            ov_user_ids = self.ov_user.search(cursor, uid, [('partner_id', '=', partner_id)])
            if ov_user_ids[0] % 2 == 0:
                return False
            return True

        mock_save_privisioning_data.side_effect = save_privisioning_data

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')

        self.assertEqual(wiz['info'], '{}: \n {}'.format(
            'Error generant contrasenyes pels següents partners',
            ','.join(['{} ({})\n'.format(str(int(x)), 'Error al guardar la contrasenya')
                     for x in ov_user_ids if x % 2 == 0])
        )
        )

    @mock.patch.object(WizardCreateChangePassword, "send_password_email")
    @mock.patch.object(WizardCreateChangePassword, "save_privisioning_data")
    def test__action_create_change_password__KO_cannot_send_password_email__even_partner_id(self, mock_save_privisioning_data, mock_send_password_email):  # noqa: E501
        ov_user_ids = self.ov_user.search(
            self.cursor,
            self.uid,
            [('active', '=', True)]
        )

        context = {'active_ids': ov_user_ids}
        wiz_id = self.wiz_o.create(self.cursor, self.uid, {}, context=context)

        mock_save_privisioning_data.return_value = True

        def send_password_email(cursor, uid, ov_user_id):
            if int(ov_user_id.id) % 2 == 0:
                raise FailSendEmail('Error text')

        mock_send_password_email.side_effect = send_password_email

        self.wiz_o.action_create_change_password(self.cursor, self.uid, [wiz_id], context=context)

        wiz = self.wiz_o.read(self.cursor, self.uid, [wiz_id])[0]

        self.assertEqual(wiz['state'], 'done')
        self.assertEqual(wiz['info'], '{}: \n {}'.format(
            'Error generant contrasenyes pels següents partners',
            ','.join(['{} ({})\n'.format(str(int(x)), "Error al generar/enviar l'email")
                     for x in ov_user_ids if x % 2 == 0])
        )
        )

    @mock.patch("tools.config.get")
    def test__save_privisioning_data__KO_without_api_key(self, mock_config):
        ov_user_id = self.ov_user.search(
            self.cursor,
            self.uid,
            [('vat', '=', 'ES48591264S')]
        )

        password = 'test-password'

        mock_config.return_value = False

        result = self.wiz_o.save_privisioning_data(self.cursor, self.uid, ov_user_id[0], password)

        self.assertFalse(result)
