# -*- encoding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from oopgrade import oopgrade
from osv import osv
from tools import config
import mock


class TestSignLead(testing.OOTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestSignLead, cls).setUpClass()
        with Transaction().start(config['db_name']) as txn:
            oopgrade.load_data(
                txn.cursor, 'som_leads_polissa', 'data/giscedata_crm_lead_data.xml', mode='update'
            )
            cls._delete_stage_validations(txn.cursor)
            txn.cursor.commit()

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
        self.patchers = []

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def _create_lead(self, cups='ES0177000000000000LR'):
        return self.lead_o.create(
            self.cursor, self.uid,
            {'name': 'Test lead / {}'.format(cups), 'cups': cups, 'state': 'open'},
            context={}
        )

    def _sign_lead(self, lead_id, cups='ES0177000000000000LR'):
        return self.www_lead_o.sign_lead(self.cursor, self.uid, lead_id, cups, context={})

    def _start_patch(self, patcher):
        self.patchers.append(patcher)
        return patcher.start()

    def _mock_signature_process(self, process_data):
        self._start_patch(mock.patch('som_leads_polissa.www.som_lead_www.Sudo'))
        cursor_mock = self._start_patch(mock.patch.object(self.www_lead_o.api.db, 'cursor'))
        cursor_mock.return_value.__enter__.return_value = self.cursor

        start_signature_mock = self._start_patch(
            mock.patch.object(self.lead_o, 'start_signature_process', return_value=123)
        )
        self._start_patch(mock.patch.object(self.process_o, 'read', return_value=process_data))
        return start_signature_mock

    def _set_signature_read(self, status):
        real_read = self.lead_o.read

        def read_signature_status(cr, uid, ids, fields=None, context=None, **kwargs):
            if fields == ['signature_process', 'status_firma']:
                return {'signature_process': [10, 'PROC'], 'status_firma': status}
            return real_read(cr, uid, ids, fields=fields, context=context, **kwargs)

        return mock.patch.object(
            self.lead_o, 'read',
            side_effect=read_signature_status
        )

    def test_sign_lead_rejects_wrong_cups(self):
        lead_id = self._create_lead()

        with self.assertRaises(osv.except_osv):
            self._sign_lead(lead_id, cups='ES999OF')

    def test_sign_lead_returns_signature_url(self):
        lead_id = self._create_lead()
        self._mock_signature_process({'signature_url': 'http://sign.url', 'status': 'done'})

        result = self._sign_lead(lead_id)

        self.assertEqual(result, {'url': 'http://sign.url'})

    def test_sign_lead_starts_signature_with_signaturit_url_context(self):
        lead_id = self._create_lead()
        start_signature_mock = self._mock_signature_process({
            'signature_url': 'http://sign.url',
            'status': 'done',
        })

        self._sign_lead(lead_id)

        context = start_signature_mock.call_args[1]['context']
        self.assertEqual(context['delivery_type'], 'url')
        self.assertEqual(context['provider'], 'signaturit')

    def test_sign_lead_raises_when_signature_process_fails(self):
        lead_id = self._create_lead()
        self._mock_signature_process({'signature_url': False, 'status': 'error'})

        with self.assertRaises(osv.except_osv):
            self._sign_lead(lead_id)

    def test_sign_lead_raises_when_signature_url_does_not_arrive(self):
        lead_id = self._create_lead()
        self._mock_signature_process({'signature_url': False, 'status': 'wait'})

        with mock.patch('som_leads_polissa.www.som_lead_www.time') as time_mock:
            time_mock.time.side_effect = [0, 31]
            with self.assertRaises(osv.except_osv):
                self._sign_lead(lead_id)

    def test_activation_mail_is_sent_when_lead_has_no_signature_process(self):
        lead_id = self._create_lead()

        with mock.patch.object(self.lead_o, '_send_mail') as send_mail_mock:
            result = self.www_lead_o._send_activation_mail_if_signature_allows(
                self.cursor, self.uid, lead_id, context={}
            )

        self.assertTrue(result)
        self.assertTrue(send_mail_mock.called)

    def test_activation_mail_is_sent_when_signature_is_completed(self):
        lead_id = self._create_lead()

        with self._set_signature_read('completed'):
            with mock.patch.object(self.lead_o, '_send_mail') as send_mail_mock:
                result = self.www_lead_o._send_activation_mail_if_signature_allows(
                    self.cursor, self.uid, lead_id, context={'skip_validations': True}
                )

        self.assertTrue(result)
        self.assertTrue(send_mail_mock.called)

    def test_activation_mail_is_not_sent_when_signature_failed(self):
        lead_id = self._create_lead()
        signature_error_stage_id = self.ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_leads_polissa', 'webform_stage_signature_error'
        )[1]

        with self._set_signature_read('error'):
            with mock.patch.object(self.lead_o, '_send_mail') as send_mail_mock:
                result = self.www_lead_o._send_activation_mail_if_signature_allows(
                    self.cursor, self.uid, lead_id, context={'skip_validations': True}
                )

        lead = self.lead_o.browse(self.cursor, self.uid, lead_id)
        self.assertFalse(result)
        self.assertFalse(send_mail_mock.called)
        self.assertEqual(lead.state, 'pending')
        self.assertEqual(lead.stage_id.id, signature_error_stage_id)

    def test_activation_mail_is_not_sent_when_signature_stays_pending(self):
        lead_id = self._create_lead()
        pending_review_stage_id = self.ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_leads_polissa', 'webform_stage_signature_pending_review'
        )[1]

        with self._set_signature_read('pending'):
            with mock.patch.object(self.lead_o, '_send_mail') as send_mail_mock:
                with mock.patch('som_leads_polissa.www.som_lead_www.time.sleep'):
                    result = self.www_lead_o._send_activation_mail_if_signature_allows(
                        self.cursor, self.uid, lead_id, context={'skip_validations': True}
                    )

        lead = self.lead_o.browse(self.cursor, self.uid, lead_id)
        self.assertFalse(result)
        self.assertFalse(send_mail_mock.called)
        self.assertEqual(lead.state, 'pending')
        self.assertEqual(lead.stage_id.id, pending_review_stage_id)
