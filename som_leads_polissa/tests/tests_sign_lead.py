# -*- encoding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from osv import osv
import mock


class TestSignLead(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def _make_mock_lead_o(self, check_result, start_result=True, signature_url=''):
        mock_lead_browse = mock.MagicMock()
        mock_lead_browse.signature_process.signature_url = signature_url

        mock_lead_o = mock.MagicMock()
        mock_lead_o.check_start_signature_process.return_value = check_result
        mock_lead_o.start_signature_process.return_value = start_result
        mock_lead_o.browse.return_value = mock_lead_browse
        return mock_lead_o

    def test_sign_lead_happy_path(self):
        www_lead_o = self.get_model('som.lead.www')
        lead_id = 42
        url = 'https://signaturit.test/url'
        mock_lead_o = self._make_mock_lead_o(('end', ''), signature_url=url)

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with mock.patch('som_leads_polissa.www.som_lead_www.Sudo') as mock_sudo:
                mock_sudo.return_value.__enter__ = mock.MagicMock(return_value=None)
                mock_sudo.return_value.__exit__ = mock.MagicMock(return_value=False)
                mock_db_cursor = mock.MagicMock()
                www_lead_o.api = mock.MagicMock()
                www_lead_o.api.db.cursor.return_value.__enter__ = mock.MagicMock(
                    return_value=mock_db_cursor)
                www_lead_o.api.db.cursor.return_value.__exit__ = mock.MagicMock(
                    return_value=False)

                result = www_lead_o.sign_lead(self.cursor, self.uid, lead_id)

        self.assertEqual(result, {'url': url})

    def test_sign_lead_invalid_lead_raises(self):
        www_lead_o = self.get_model('som.lead.www')
        lead_id = 42
        mock_lead_o = self._make_mock_lead_o(('error', 'Lead no pot firmar'))

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with self.assertRaises(osv.except_osv):
                www_lead_o.sign_lead(self.cursor, self.uid, lead_id)

        mock_lead_o.start_signature_process.assert_not_called()

    def test_sign_lead_passes_fixed_context(self):
        www_lead_o = self.get_model('som.lead.www')
        lead_id = 42
        url = 'https://signaturit.test/url'
        mock_lead_o = self._make_mock_lead_o(('end', ''), signature_url=url)

        with mock.patch.object(www_lead_o.pool, 'get', return_value=mock_lead_o):
            with mock.patch('som_leads_polissa.www.som_lead_www.Sudo') as mock_sudo:
                mock_sudo.return_value.__enter__ = mock.MagicMock(return_value=None)
                mock_sudo.return_value.__exit__ = mock.MagicMock(return_value=False)
                www_lead_o.api = mock.MagicMock()
                mock_db_cursor = mock.MagicMock()
                www_lead_o.api.db.cursor.return_value.__enter__ = mock.MagicMock(
                    return_value=mock_db_cursor)
                www_lead_o.api.db.cursor.return_value.__exit__ = mock.MagicMock(
                    return_value=False)

                www_lead_o.sign_lead(self.cursor, self.uid, lead_id)

        call_args = mock_lead_o.check_start_signature_process.call_args
        ctx_passed = call_args[1].get('context', {})
        self.assertEqual(ctx_passed.get('delivery_type'), 'url')
        self.assertEqual(ctx_passed.get('provider'), 'signaturit')
