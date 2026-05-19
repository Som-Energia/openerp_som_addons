# -*- encoding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from osv import osv
from tools import config
import mock


class TestSignLead(testing.OOTestCase):

    @classmethod
    def tearDownClass(cls):
        with Transaction().start(config['db_name']) as txn:
            val_o = cls.openerp.pool.get('crm.stage.validation')
            ids = val_o.search(txn.cursor, 1, [])
            val_o.unlink(txn.cursor, 1, ids)
            txn.cursor.commit()
        super(TestSignLead, cls).tearDownClass()

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def test_sign_lead_returns_url_with_signaturit_context(self):
        www_lead_o = self.get_model('som.lead.www')
        mock_lead_o = mock.MagicMock()
        mock_lead_o.check_start_signature_process.return_value = ('end', '')
        mock_lead_o.start_signature_process.return_value = 123
        mock_lead_o.read.return_value = {
            'signature_url': 'http://sign.url',
            'status': 'done'
        }

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with mock.patch('som_leads_polissa.www.som_lead_www.Sudo'):
                result = www_lead_o.sign_lead(self.cursor, self.uid, 1)

        self.assertEqual(result, {'url': 'http://sign.url'})
        ctx_passed = mock_lead_o.check_start_signature_process.call_args[1]['context']
        self.assertEqual(ctx_passed.get('delivery_type'), 'url')
        self.assertEqual(ctx_passed.get('provider'), 'signaturit')
        mock_lead_o.read.assert_called_with(
            self.cursor, self.uid, 123, ['signature_url', 'status'], context={}
        )

    def test_sign_lead_invalid_lead_raises(self):
        www_lead_o = self.get_model('som.lead.www')
        mock_lead_o = mock.MagicMock()
        mock_lead_o.check_start_signature_process.return_value = ('error', 'Lead no pot firmar')

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with self.assertRaises(osv.except_osv):
                www_lead_o.sign_lead(self.cursor, self.uid, 1)

        mock_lead_o.start_signature_process.assert_not_called()

    def test_sign_lead_timeout_raises(self):
        www_lead_o = self.get_model('som.lead.www')
        mock_lead_o = mock.MagicMock()
        mock_lead_o.check_start_signature_process.return_value = ('end', '')
        mock_lead_o.start_signature_process.return_value = 123
        mock_lead_o.read.return_value = {
            'signature_url': False,
            'status': 'wait'
        }

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with mock.patch('som_leads_polissa.www.som_lead_www.Sudo'):
                with mock.patch('som_leads_polissa.www.som_lead_www.time.sleep'):
                    with mock.patch(
                        'som_leads_polissa.www.som_lead_www.time.time',
                        side_effect=[0, 1, 31]
                    ):
                        with self.assertRaises(osv.except_osv):
                            www_lead_o.sign_lead(self.cursor, self.uid, 1)

        mock_lead_o.read.assert_called_with(
            self.cursor, self.uid, 123, ['signature_url', 'status'], context={}
        )

    def test_send_activation_mail_waits_until_signature_completed(self):
        www_lead_o = self.get_model('som.lead.www')
        mock_lead_o = mock.MagicMock()
        mock_lead_o.read.side_effect = [
            {'signature_process': [10, 'PROC'], 'status_firma': 'pending'},
            {'signature_process': [10, 'PROC'], 'status_firma': 'completed'},
        ]

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with mock.patch('som_leads_polissa.www.som_lead_www.time.sleep'):
                res = www_lead_o._send_activation_mail_if_signature_allows(
                    self.cursor, self.uid, 1, context={}
                )

        self.assertTrue(res)
        self.assertEqual(mock_lead_o.read.call_count, 2)
        mock_lead_o._send_mail.assert_called_once_with(self.cursor, self.uid, 1, context={})

    def test_send_activation_mail_not_sent_when_signature_failed(self):
        www_lead_o = self.get_model('som.lead.www')
        mock_lead_o = mock.MagicMock()
        mock_lead_o.read.return_value = {
            'signature_process': [10, 'PROC'],
            'status_firma': 'error',
        }

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            res = www_lead_o._send_activation_mail_if_signature_allows(
                self.cursor, self.uid, 1, context={}
            )

        self.assertFalse(res)
        mock_lead_o._send_mail.assert_not_called()
        mock_lead_o.write.assert_called_once()
        mock_lead_o.historize_msg.assert_called_once()

    def test_send_activation_mail_sets_pending_review_when_signature_never_arrives(self):
        www_lead_o = self.get_model('som.lead.www')
        mock_lead_o = mock.MagicMock()
        mock_ir_model_o = mock.MagicMock()
        mock_ir_model_o.get_object_reference.return_value = [1, 999]
        mock_lead_o.read.return_value = {
            'signature_process': [10, 'PROC'],
            'status_firma': 'pending',
        }

        def _pool_get(model_name):
            if model_name == 'ir.model.data':
                return mock_ir_model_o
            return mock_lead_o

        with mock.patch.object(www_lead_o.pool, 'get', side_effect=_pool_get):
            with mock.patch('som_leads_polissa.www.som_lead_www.time.sleep'):
                res = www_lead_o._send_activation_mail_if_signature_allows(
                    self.cursor, self.uid, 1, context={}
                )

        self.assertFalse(res)
        mock_lead_o._send_mail.assert_not_called()
        mock_lead_o.write.assert_called_once_with(
            self.cursor, self.uid, 1,
            {'stage_id': 999, 'state': 'pending'},
            context={}
        )
        mock_lead_o.historize_msg.assert_called_once()
