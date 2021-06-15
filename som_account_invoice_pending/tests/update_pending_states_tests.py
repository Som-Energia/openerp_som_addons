# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import date, timedelta
import mock
from mock import Mock, ANY
from ..som_account_invoice_pending_exceptions import UpdateWaitingFor48hException, \
    UpdateWaitingCancelledContractsException, UpdateWaitingForAnnexIVException


class TestUpdatePendingStates(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestUpdatePendingStates, self).setUp()
        self.pool = self.openerp.pool
        self._load_demo_data(self.cursor, self.uid)

    def tearDown(self):
        self.txn.stop()

    def _load_demo_data(self, cursor, uid):
        imd_obj = self.pool.get('ir.model.data')

        self.account_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'cobraments_mail_account'
        )[1]

        self.annex3_template_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'email_impagats_annex3'
        )[1]

        self.annex4_template_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'email_impagats_annex4'
        )[1]

        self.email_48h_template_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'email_impagats_48h'
        )[1]

        self.sms_annex4_template_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'sms_template_annex4'
        )[1]

        self.sms_48h_template_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'sms_template_48h_tall'
        )[1]

        self.invoice_1_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0001'
        )[1]
        self.invoice_2_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'factura_0002'
        )[1]

        self.correct_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'correct_bono_social_pending_state'
        )[1]

        self.waiting_annexII = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'pendent_avis_previ_inici_procediment_pending_state'
        )[1]

        self.annexII_sent = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'avis_previ_inici_procediment_enviat_pending_state'
        )[1]

        self.waiting_annexIII_first = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'carta_1_pendent_pending_state'
        )[1]

        self.annexIII_first_sent = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'carta_1_pending_state'
        )[1]

        self.waiting_annexIII_second = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'carta_2_pendent_pending_state'
        )[1]

        self.annexIII_second_sent = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'carta_2_pending_state'
        )[1]

        self.waiting_annexIV_def = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'default_pendent_carta_avis_tall_pending_state'
        )[1]

        self.annexIV_sent_def = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'default_carta_avis_tall_pending_state'
        )[1]

        self.waiting_annexIV_bs = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'pendent_carta_avis_tall_pending_state'
        )[1]

        self.annexIV_sms_template_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'sms_template_annex4'
        )[1]

        self.annexIV_sent_bs = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'carta_avis_tall_pending_state'
        )[1]

        self.waiting_48h_def = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'default_pendent_notificacio_tall_imminent_pending_state'
        )[1]

        self.waiting_48h_bs = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pendent_notificacio_tall_imminent_pending_state'
        )[1]

        self.sent_48h_def = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'default_notificacio_tall_imminent_enviada_pending_state'
        )[1]

        self.sent_48h_bs = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'notificacio_tall_imminent_enviada_pending_state'
        )[1]

        self.waiting_unpaid_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'esperant_segona_factura_impagada_pending_state'
        )[1]

        self.def_correct_id = imd_obj.get_object_reference(
            cursor, uid, 'account_invoice_pending',
            'default_invoice_pending_state'
        )[1]

        self.def_waiting_unpaid_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'default_esperant_segona_factura_impagada_pending_state'
        )[1]

    def _load_data_unpaid_invoices(self, cursor, uid, invoice_semid_list=[]):
        imd_obj = self.pool.get('ir.model.data')
        inv_obj = self.pool.get('account.invoice')
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        contract_name = ''
        for index, res_id in enumerate(invoice_semid_list, start=1):
            fact_id = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio', 'factura_000'+str(index)
            )[1]
            invoice_id = fact_obj.read(cursor, uid, fact_id, ['invoice_id'])['invoice_id'][0]

            if index == 1:
                contract_name = inv_obj.read(cursor, uid, invoice_id, ['name'])['name']

            inv_obj.write(cursor, uid, invoice_id, {
                'name': contract_name,
            })
            inv_obj.set_pending(cursor, uid, [invoice_id], res_id)

    def test__update_second_unpaid_invoice__two_invoices_moving(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_unpaid_id, self.waiting_unpaid_id])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_unpaid_id)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_unpaid_id)

        pending_obj.update_second_unpaid_invoice(cursor, uid)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)

    def test__update_second_unpaid_invoice__two_invoices_not_moving(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.def_correct_id, self.def_waiting_unpaid_id])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.def_correct_id)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.def_waiting_unpaid_id)

        pending_obj.update_second_unpaid_invoice(cursor, uid)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.def_correct_id)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.def_waiting_unpaid_id)

    def test__update_second_unpaid_invoice__one_unpaid_invoice_not_moving(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.def_waiting_unpaid_id])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.def_waiting_unpaid_id)

        pending_obj.update_second_unpaid_invoice(cursor, uid)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.def_waiting_unpaid_id)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    def test__update_unpaid_invoice_waiting_for_annexII(self, mock_function):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexII])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexII)

        pending_obj.update_waiting_for_annexII(cursor, uid)

        mock_function.assert_called_once()

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexII_sent)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    def test__update_two_unpaid_invoice_waiting_for_annexII_same_contract(self, mock_function):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexII, self.waiting_annexII])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexII)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexII)

        pending_obj.update_waiting_for_annexII(cursor, uid)

        self.assertEqual(mock_function.call_count, 2)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexII_sent)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.annexII_sent)

    def test__update_unpaid_invoice_waiting_for_annexIII_first_no_update(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.annexII_sent])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexII_sent)

        pending_obj.update_waiting_for_annexIII_first(cursor, uid)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertNotEqual(inv_data.pending_state.id, self.annexIII_first_sent)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    def test__update_unpaid_invoice_waiting_for_annexIII_first_one_invoice(self, mock_function):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIII_first])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIII_first)

        pending_obj.update_waiting_for_annexIII_first(cursor, uid)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexIII_first_sent)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    def test__update_unpaid_invoice_waiting_annexIII_first_email_unsend(self, mock_function):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIII_first])

        mock_function.return_value = -1

        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIII_first)

        pending_obj.update_waiting_for_annexIII_first(cursor, uid)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIII_first)

    def test__update_unpaid_invoice_waiting_for_annexIII_second_no_update(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.annexII_sent])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexII_sent)

        pending_obj.update_waiting_for_annexIII_second(cursor, uid)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertNotEqual(inv_data.pending_state.id, self.annexIII_second_sent)

    def test__update_unpaid_invoice_waiting_for_annexIII_second_one_invoice(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIII_second])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIII_second)

        pending_obj.update_waiting_for_annexIII_second(cursor, uid)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexIII_second_sent)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    def test__update_unpaid_invoice_waiting_annexIII_second_email_unsend(self, mock_function):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIII_second])

        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIII_second)
        mock_function.return_value = -1

        pending_obj.update_waiting_for_annexIII_second(cursor, uid)

        params = {
            'email_from': self.account_id,
            'template_id': self.annex3_template_id,
        }
        mock_function.assert_called_once_with(cursor, uid, self.invoice_1_id, params)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIII_second)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_unpaid_invoice_waiting_for_annexIV_def(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIV_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)

        pending_obj.update_waiting_for_annexIV(cursor, uid)

        send_mail_params = {
            'email_from': self.account_id,
            'template_id': self.annex4_template_id,
        }

        mock_mail.assert_called_once_with(cursor, uid, self.invoice_1_id, send_mail_params)
        mock_sms.assert_called_once_with(cursor, uid, self.invoice_1_id,
                                         self.sms_annex4_template_id, self.waiting_annexIV_def, {})

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexIV_sent_def)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_unpaid_invoice_waiting_for_annexIV_bs(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIV_bs])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_bs)

        pending_obj.update_waiting_for_annexIV(cursor, uid)

        params = {
            'email_from': self.account_id,
            'template_id': self.annex4_template_id,
        }

        mock_mail.assert_called_once_with(cursor, uid, self.invoice_1_id, params)
        mock_sms.assert_called_once_with(cursor, uid, self.invoice_1_id,
                                         self.sms_annex4_template_id, self.waiting_annexIV_bs, {})

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexIV_sent_bs)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_two_unpaid_invoice_waiting_for_annexIV_same_contract(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIV_def, self.waiting_annexIV_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)

        pending_obj.update_waiting_for_annexIV(cursor, uid)

        params = {
            'email_from': self.account_id,
            'template_id': self.annex4_template_id,
        }

        self.assertEqual(mock_mail.call_count, 2)
        self.assertEqual(mock_sms.call_count, 1)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexIV_sent_def)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.annexIV_sent_def)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_unpaid_invoice_waiting_for_48h_def(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)

        pending_obj.update_waiting_for_48h(cursor, uid)

        send_mail_params = {
            'email_from': self.account_id,
            'template_id': self.email_48h_template_id,
        }

        mock_mail.assert_called_once_with(cursor, uid, self.invoice_1_id, send_mail_params)
        mock_sms.assert_called_once_with(cursor, uid, self.invoice_1_id,
                                         self.sms_48h_template_id, self.waiting_48h_def, {})

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.sent_48h_def)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_unpaid_invoice_waiting_for_48_bs(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_bs])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)

        pending_obj.update_waiting_for_48h(cursor, uid)

        send_mail_params = {
            'email_from': self.account_id,
            'template_id': self.email_48h_template_id,
        }

        mock_mail.assert_called_once_with(cursor, uid, self.invoice_1_id, send_mail_params)
        mock_sms.assert_called_once_with(cursor, uid, self.invoice_1_id,
                                         self.sms_48h_template_id, self.waiting_48h_bs, {})

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.sent_48h_bs)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_two_unpaid_invoice_waiting_for_48_same_contract_single_sms(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_def, self.waiting_48h_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)

        pending_obj.update_waiting_for_48h(cursor, uid)

        params = {
            'email_from': self.account_id,
            'template_id': self.email_48h_template_id,
        }

        mock_mail.assert_called_with(cursor, uid, self.invoice_2_id, params)
        mock_sms.assert_called_once_with(cursor, uid, ANY,
                                    self.sms_48h_template_id, self.waiting_48h_def, {})

        self.assertEqual(mock_mail.call_count, 2)
        self.assertEqual(mock_sms.call_count, 1)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.sent_48h_def)
        inv_data = fact_obj.browse(cursor, uid, self.invoice_2_id)
        self.assertEqual(inv_data.pending_state.id, self.sent_48h_def)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_two_unpaid_invoice_bs_waiting_for_48_raisesError(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_bs])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)

        with mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_48h_active_contracts') as updateMock:
            updateMock.side_effect = UpdateWaitingFor48hException('test')
            with self.assertRaises(UpdateWaitingFor48hException) as context:
                pending_obj.update_waiting_for_48h_active_contracts(cursor, uid)

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)

        with mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_48h_active_contracts') as updateMock:
            updateMock.side_effect = Exception('general exception test')
            with self.assertRaises(Exception) as context:
                pending_obj.update_waiting_for_48h_active_contracts(cursor, uid)

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)

        pending_obj.update_waiting_for_48h(cursor, uid)
        self.assertEqual(mock_mail.call_count, 1)
        self.assertEqual(mock_sms.call_count, 1)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.sent_48h_bs)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_two_unpaid_invoice_dp_waiting_for_48_raisesError(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)

        with mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_48h_active_contracts') as updateMock:
            updateMock.side_effect = UpdateWaitingFor48hException('test')
            with self.assertRaises(UpdateWaitingFor48hException) as context:
                pending_obj.update_waiting_for_48h_active_contracts(cursor, uid)

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)

        with mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_48h_active_contracts') as send_SMSMock:
            send_SMSMock.side_effect = Exception('general exception test')
            with self.assertRaises(Exception) as context:
                pending_obj.update_waiting_for_48h_active_contracts(cursor, uid)

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)

        pending_obj.update_waiting_for_48h(cursor, uid)
        self.assertEqual(mock_mail.call_count, 1)
        self.assertEqual(mock_sms.call_count, 1)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.sent_48h_def)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_waiting_48h_invoice_bs_polissa_baixa_raisesError(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_bs])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)

        pol_id = inv_data.polissa_id.id
        pol_obj.write(cursor, uid, [pol_id], {'state': 'baixa'})

        with mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_annex_cancelled_contracts') as send_SMSMock:
            send_SMSMock.side_effect = UpdateWaitingCancelledContractsException('test')

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_48h_bs)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_waiting_48h_invoice_dp_polissa_baixa_raisesError(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)

        pol_id = inv_data.polissa_id.id
        pol_obj.write(cursor, uid, [pol_id], {'state': 'baixa'})

        with mock.patch(
                'som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_annex_cancelled_contracts') as send_SMSMock:
            send_SMSMock.side_effect = UpdateWaitingCancelledContractsException('test')

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_48h_def)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_waiting_annexIV_invoice_bs_polissa_baixa_raisesError(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIV_bs])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_bs)

        pol_id = inv_data.polissa_id.id
        pol_obj.write(cursor, uid, [pol_id], {'state': 'baixa'})

        with mock.patch(
                'som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_annex_cancelled_contracts') as send_SMSMock:
            send_SMSMock.side_effect = UpdateWaitingCancelledContractsException('test')

            pending_obj.update_waiting_for_annexIV(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_bs)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_waiting_annexIV_invoice_dp_polissa_baixa_raisesError(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIV_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)

        pol_id = inv_data.polissa_id.id
        pol_obj.write(cursor, uid, [pol_id], {'state': 'baixa'})

        with mock.patch(
                'som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_annex_cancelled_contracts') as send_SMSMock:
            send_SMSMock.side_effect = UpdateWaitingCancelledContractsException('test')

            pending_obj.update_waiting_for_annexIV(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__update_two_unpaid_invoice_dp_waiting_for_annexIV_raisesError(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIV_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)

        with mock.patch(
                'som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_annexIV_active_contracts') as send_SMSMock:
            send_SMSMock.side_effect = UpdateWaitingForAnnexIVException('test')
            with self.assertRaises(UpdateWaitingForAnnexIVException) as context:
                pending_obj.update_waiting_for_annexIV_active_contracts(cursor, uid)

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)

        with mock.patch(
                'som_account_invoice_pending.update_pending_states.UpdatePendingStates.update_waiting_for_annexIV_active_contracts') as updateMock:
            updateMock.side_effect = Exception('general exception test')
            with self.assertRaises(Exception) as context:
                pending_obj.update_waiting_for_annexIV_active_contracts(cursor, uid)

            pending_obj.update_waiting_for_48h(cursor, uid)

            self.assertEqual(mock_mail.call_count, 0)
            self.assertEqual(mock_sms.call_count, 0)

            inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
            self.assertEqual(inv_data.pending_state.id, self.waiting_annexIV_def)

        pending_obj.update_waiting_for_annexIV(cursor, uid)
        self.assertEqual(mock_mail.call_count, 1)
        self.assertEqual(mock_sms.call_count, 1)

        inv_data = fact_obj.browse(cursor, uid, self.invoice_1_id)
        self.assertEqual(inv_data.pending_state.id, self.annexIV_sent_def)


    def test__integration_send_email(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_def, self.waiting_48h_def])
        pending_obj = self.pool.get('update.pending.states')
        pending_obj.update_waiting_for_48h(cursor, uid)

        pem_obj = self.pool.get('poweremail.mailbox')
        mail_to_send = pem_obj.search(cursor, uid, [
            ('pem_account_id', '=', self.account_id),
            ('pem_subject', 'like', 'Corte de luz / Tall de llum'),
        ])
        self.assertEqual(len(mail_to_send), 2)

    def test__integration_send_sms(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_def, self.waiting_48h_def])
        pending_obj = self.pool.get('update.pending.states')
        pending_obj.update_waiting_for_48h(cursor, uid, context={'create_empty_number': True})

        psms_obj = self.pool.get('powersms.smsbox')
        sms_to_send = psms_obj.search(cursor, uid, [
            ('psms_from', 'like', 'Info'),
            ('psms_body_text', 'ilike', '%CORTE LUZ POR IMPAGO EN 48h%'),
        ])
        self.assertEqual(len(sms_to_send), 1)

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__sms_callback_historize_annexIV(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_annexIV_def,self.waiting_annexIV_def])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        aiph_obj = self.pool.get('account.invoice.pending.history')

        pending_obj.update_waiting_for_annexIV(cursor, uid)

        self.assertEqual(mock_mail.call_count, 2)
        self.assertEqual(mock_sms.call_count, 1)


        first_inv = min(self.invoice_1_id, self.invoice_2_id)
        last_inv = max(self.invoice_1_id, self.invoice_2_id)

        last_pending_id = min(fact_obj.read(cursor, uid, last_inv, ['pending_history_ids'])['pending_history_ids'])
        last_pending = aiph_obj.browse(cursor, uid, last_pending_id)

        self.assertEqual(last_pending.observations,
                         u'Comunicació feta a través de la factura amb id:{}'.format(first_inv))

    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_email')
    @mock.patch('som_account_invoice_pending.update_pending_states.UpdatePendingStates.send_sms')
    def test__sms_callback_historize_48h(self, mock_sms, mock_mail):
        cursor = self.txn.cursor
        uid = self.txn.user
        self._load_data_unpaid_invoices(cursor, uid, [self.waiting_48h_bs, self.waiting_48h_bs])
        pending_obj = self.pool.get('update.pending.states')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        aiph_obj = self.pool.get('account.invoice.pending.history')

        pending_obj.update_waiting_for_48h(cursor, uid)

        self.assertEqual(mock_mail.call_count, 2)
        self.assertEqual(mock_sms.call_count, 1)

        first_inv = min(self.invoice_1_id, self.invoice_2_id)
        last_inv = max(self.invoice_1_id, self.invoice_2_id)

        last_pending_id = min(fact_obj.read(cursor, uid, last_inv, ['pending_history_ids'])['pending_history_ids'])
        last_pending = aiph_obj.browse(cursor, uid, last_pending_id)

        self.assertEqual(last_pending.observations,
                         u'Comunicació feta a través de la factura amb id:{}'.format(first_inv))
