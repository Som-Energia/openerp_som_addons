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
        mock_lead_o.browse.return_value.signature_process.signature_url = 'http://sign.url'

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with mock.patch('som_leads_polissa.www.som_lead_www.Sudo'):
                with mock.patch('ctx.current_session'):
                    result = www_lead_o.sign_lead(self.cursor, self.uid, 1)

        self.assertEqual(result, {'url': 'http://sign.url'})
        ctx_passed = mock_lead_o.check_start_signature_process.call_args[1]['context']
        self.assertEqual(ctx_passed.get('delivery_type'), 'url')
        self.assertEqual(ctx_passed.get('provider'), 'signaturit')

    def test_sign_lead_invalid_lead_raises(self):
        www_lead_o = self.get_model('som.lead.www')
        mock_lead_o = mock.MagicMock()
        mock_lead_o.check_start_signature_process.return_value = ('error', 'Lead no pot firmar')

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with self.assertRaises(osv.except_osv):
                www_lead_o.sign_lead(self.cursor, self.uid, 1)

        mock_lead_o.start_signature_process.assert_not_called()
