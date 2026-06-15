# -*- encoding: utf-8 -*-
import copy

from destral import testing
from destral.transaction import Transaction
from osv import osv
from tools import config
import mock

from .base_som_lead_www import BaseSomLeadWwwTest


class TestSignLead(testing.OOTestCase):

    _signaturit_start_fnc = (
        'giscedata_signatura_documents_signaturit.giscedata_signatura_documents.'
        'GiscedataSignaturaProcess.start'
    )
    _cups = 'ES0177000000000000LR'

    @classmethod
    def tearDownClass(cls):
        with Transaction().start(config['db_name']) as txn:
            cls._delete_stage_validations(txn.cursor)
            txn.cursor.commit()
        super(TestSignLead, cls).tearDownClass()

    @classmethod
    def _delete_stage_validations(cls, cursor):
        val_o = cls.openerp.pool.get('crm.stage.validation')
        ids = val_o.search(cursor, 1, [])
        val_o.unlink(cursor, 1, ids)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.www_lead_o = self.get_model('som.lead.www')
        self.lead_o = self.get_model('giscedata.crm.lead')
        self.process_o = self.get_model('giscedata.signatura.process')
        self.ir_model_o = self.get_model('ir.model.data')
        self.config_o = self.get_model('res.config')
        self.payment_mode_o = self.get_model('payment.mode')
        self._delete_stage_validations(self.cursor)
        self.config_o.set(self.cursor, self.uid, 'validar_lead_firmar_digitalment', 0)

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def _create_lead(self, cups=None):
        cups = cups or self._cups
        stage_id = self.ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_leads_polissa', 'webform_stage_recieved'
        )[1]
        payment_mode_id = self.payment_mode_o.search(
            self.cursor, self.uid, [('name', '=', 'ENGINYERS')]
        )[0]
        lead_id = self.lead_o.create(
            self.cursor, self.uid,
            {
                'name': 'Test lead / {}'.format(cups),
                'cups': cups,
                'stage_id': stage_id,
                'state': 'open',
                'lang': 'en_US',
                'titular_email': 'test@example.org',
                'titular_nom': 'Test titular',
                'payment_mode_id': payment_mode_id,
            },
            context={}
        )
        self.cursor.commit()
        return lead_id

    def _signaturit_start_side_effect(self, signature_url='http://sign.url', status='wait'):
        def start(cr, uid, ids, context=None):
            self.process_o.write(
                cr, uid, ids,
                {'signature_url': signature_url, 'status': status},
                context=context
            )
            return True

        return start

    def test_sign_lead_rejects_wrong_cups(self):
        lead_id = self._create_lead()

        with self.assertRaises(osv.except_osv):
            self.www_lead_o.sign_lead(self.cursor, self.uid, lead_id, 'ES999OF', context={})

    @mock.patch(_signaturit_start_fnc)
    def test_sign_lead_returns_signature_url(self, signaturit_start_mock):
        signaturit_start_mock.side_effect = self._signaturit_start_side_effect()
        lead_id = self._create_lead()

        result = self.www_lead_o.sign_lead(
            self.cursor, self.uid, lead_id, self._cups, context={'skip_validations': True}
        )

        self.assertEqual(result, {'url': 'http://sign.url'})

    @mock.patch(_signaturit_start_fnc)
    def test_sign_lead_starts_signature_with_signaturit_url_context(self, signaturit_start_mock):
        signaturit_start_mock.side_effect = self._signaturit_start_side_effect()
        lead_id = self._create_lead()

        self.www_lead_o.sign_lead(
            self.cursor, self.uid, lead_id, self._cups, context={'skip_validations': True}
        )

        context = signaturit_start_mock.call_args[1]['context']
        self.assertEqual(context['delivery_type'], 'url')
        self.assertEqual(context['provider'], 'signaturit')

    @mock.patch(_signaturit_start_fnc)
    def test_sign_lead_raises_when_signature_url_does_not_arrive(self, signaturit_start_mock):
        signaturit_start_mock.side_effect = self._signaturit_start_side_effect(
            signature_url=False, status='wait'
        )
        lead_id = self._create_lead()

        with mock.patch('som_leads_polissa.www.som_lead_www.time') as time_mock:
            time_mock.time.side_effect = [0, 31]
            with self.assertRaises(osv.except_osv):
                self.www_lead_o.sign_lead(
                    self.cursor, self.uid, lead_id, self._cups,
                    context={'skip_validations': True}
                )


class TestActivationMailAfterSignature(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.www_lead_o = self.get_model('som.lead.www')

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def _mock_lead(self, signature_status):
        lead_o = mock.MagicMock()
        lead_o.read.return_value = {
            'signature_process': [10, 'PROC'],
            'status_firma': signature_status,
        }
        return lead_o

    def test_activation_mail_is_sent_when_signature_is_completed(self):
        lead_o = self._mock_lead('completed')

        with mock.patch.object(self.www_lead_o.pool, 'get', return_value=lead_o):
            result = self.www_lead_o._send_activation_mail_if_signature_allows(
                self.cursor, self.uid, 1, context={}
            )

        self.assertTrue(result)
        lead_o._send_mail.assert_called_once_with(self.cursor, self.uid, 1, context={})

    def test_activation_mail_is_not_sent_when_signature_failed(self):
        lead_o = self._mock_lead('error')

        with mock.patch.object(self.www_lead_o.pool, 'get', return_value=lead_o):
            result = self.www_lead_o._send_activation_mail_if_signature_allows(
                self.cursor, self.uid, 1, context={}
            )

        self.assertFalse(result)
        lead_o._send_mail.assert_not_called()
        lead_o.write.assert_called_once()
        lead_o.historize_msg.assert_called_once()

    def test_activation_mail_sets_pending_review_when_signature_never_arrives(self):
        lead_o = self._mock_lead('pending')
        ir_model_o = mock.MagicMock()
        ir_model_o.get_object_reference.return_value = [1, 999]

        def pool_get(model_name):
            if model_name == 'ir.model.data':
                return ir_model_o
            return lead_o

        with mock.patch.object(self.www_lead_o.pool, 'get', side_effect=pool_get):
            with mock.patch('som_leads_polissa.www.som_lead_www.time.sleep'):
                result = self.www_lead_o._send_activation_mail_if_signature_allows(
                    self.cursor, self.uid, 1, context={}
                )

        self.assertFalse(result)
        lead_o._send_mail.assert_not_called()
        lead_o.write.assert_called_once_with(
            self.cursor, self.uid, 1,
            {'stage_id': 999, 'state': 'pending'},
            context={}
        )
        lead_o.historize_msg.assert_called_once()


class TestCreateLeadWithSignature(BaseSomLeadWwwTest):

    def test_create_lead_returns_signature_metadata(self):
        www_lead_o = self.get_model('som.lead.www')
        values = copy.deepcopy(self._basic_values)
        values['signature'] = True

        with mock.patch.object(
            www_lead_o, 'sign_lead', return_value={'url': 'http://sign.url'}
        ) as sign_mock:
            result = www_lead_o.create_lead(self.cursor, self.uid, values, context={})

        self.assertFalse(result['error'])
        self.assertEqual(result['signature_url'], 'http://sign.url')
        self.assertEqual(result['signature_provider'], 'signaturit')
        sign_mock.assert_called_once_with(
            self.cursor, self.uid, result['lead_id'],
            values['contract_info']['cups'], context={}
        )

    def test_create_lead_keeps_lead_and_returns_signature_error(self):
        www_lead_o = self.get_model('som.lead.www')
        lead_o = self.get_model('giscedata.crm.lead')
        ir_model_o = self.get_model('ir.model.data')
        values = copy.deepcopy(self._basic_values)
        values['signature'] = True

        with mock.patch.object(
            www_lead_o, 'sign_lead', side_effect=osv.except_osv('Error', 'No pot firmar')
        ):
            result = www_lead_o.create_lead(self.cursor, self.uid, values, context={})

        signature_error_stage_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_leads_polissa', 'webform_stage_signature_error'
        )[1]
        lead = lead_o.browse(self.cursor, self.uid, result['lead_id'], context={})

        self.assertEqual(result['error']['error'], 'No pot firmar')
        self.assertFalse(result['signature_url'])
        self.assertFalse(result['signature_provider'])
        self.assertEqual(lead.stage_id.id, signature_error_stage_id)
