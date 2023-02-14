# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from osv import osv
from datetime import datetime
import poweremail
import mock


class TestWizardBaixaSoci(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.Investment = self.openerp.pool.get('generationkwh.investment')
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.Soci = self.openerp.pool.get('somenergia.soci')
        self.WizardBaixaSoci = self.openerp.pool.get('wizard.baixa.soci')
        self.AccountObj = self.openerp.pool.get('poweremail.core_accounts')

    def tearDown(self):
        self.txn.stop()

    @mock.patch("som_generationkwh.somenergia_soci.SomenergiaSoci.arxiva_socia_mailchimp_async")
    def test__baixa_soci__allowed(self, mailchimp_mock):
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0003'
        )[1]
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        context = {'active_ids':[member_id]}

        wiz_id = self.WizardBaixaSoci.create(self.cursor, self.uid, {'info':''}, context=context)
        self.WizardBaixaSoci.baixa_soci(self.cursor, self.uid, wiz_id, context=context, send_mail=False)

        baixa = self.Soci.read(self.cursor, self.uid, member_id, ['baixa'])['baixa']
        self.assertTrue(baixa)
        mailchimp_mock.assert_called_with(self.cursor, self.uid, member_id)

    def test__baixa_soci__notAllowed(self):
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
        )[1]
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        context = {'active_ids':[member_id]}

        wiz_id = self.WizardBaixaSoci.create(self.cursor, self.uid, {'info':''}, context=context)
        self.WizardBaixaSoci.baixa_soci(self.cursor, self.uid, wiz_id, context=context, send_mail=False)

        baixa = self.Soci.read(self.cursor, self.uid, member_id, ['baixa'])['baixa']
        self.assertFalse(baixa)

    @mock.patch("som_generationkwh.somenergia_soci.SomenergiaSoci.arxiva_socia_mailchimp_async")
    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__baixa_soci_and_send_mail__allowed(self, mocked_send_mail, mailchimp_mock):
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0003'
        )[1]
        template_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'email_baixa_soci'
        )[1]
        email_from = self.AccountObj.search(self.cursor, self.uid, [('name', 'ilike', 'Info%Som Energia')])[0]
        self.AccountObj.write(self.cursor, self.uid, email_from, {'name': 'Info Som Energia'})
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})
        context = {'active_ids':[member_id]}

        wiz_id = self.WizardBaixaSoci.create(self.cursor, self.uid, {'info':''}, context=context)
        self.WizardBaixaSoci.baixa_soci(self.cursor, self.uid, wiz_id, context=context, send_mail=True)

        baixa = self.Soci.read(self.cursor, self.uid, member_id, ['baixa'])['baixa']
        self.assertTrue(baixa)

        expected_ctx = {
                'active_ids': [member_id],
                'active_id': member_id,
                'template_id': template_id,
                'src_model': 'somenergia.soci',
                'src_rec_ids': [member_id],
                'from': email_from,
                'state': 'single',
                'priority': '0',
            }

        mocked_send_mail.assert_called_with(self.cursor, self.uid, mock.ANY, expected_ctx)
        mailchimp_mock.assert_called_with(self.cursor, self.uid, member_id)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__baixa_soci_and_send_mail__notAllowed(self, mocked_send_mail):
        member_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'som_generationkwh', 'soci_0001'
        )[1]
        self.Soci.write(self.cursor, self.uid, [member_id], {'baixa': False, 'data_baixa_soci': None})

        context = {'active_ids':[member_id]}

        wiz_id = self.WizardBaixaSoci.create(self.cursor, self.uid, {'info':''}, context=context)
        self.WizardBaixaSoci.baixa_soci_and_send_mail(self.cursor, self.uid, wiz_id, context=context)

        baixa = self.Soci.read(self.cursor, self.uid, member_id, ['baixa'])['baixa']
        self.assertFalse(baixa)
        mocked_send_mail.assert_not_called()