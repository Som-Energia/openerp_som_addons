# -*- encoding: utf-8 -*-
from __future__ import absolute_import


from destral import testing
from destral.transaction import Transaction
from osv import osv
import mock


class TestSignLead(testing.OOTestCase):

    _signaturit_start_fnc = (
        'giscedata_signatura_documents_signaturit.giscedata_signatura_documents.'
        'GiscedataSignaturaProcess.start'
    )
    _cups = 'ES0177000000000000LR'

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

        with mock.patch.object(
            self.lead_o, 'check_start_signature_process', return_value=('end', '')
        ):
            result = self.www_lead_o.sign_lead(
                self.cursor, self.uid, lead_id, self._cups,
                context={'skip_validations': True}
            )

        self.assertEqual(result, {'url': 'http://sign.url'})

    @mock.patch(_signaturit_start_fnc)
    def test_sign_lead_starts_signature_with_signaturit_url_context(self, signaturit_start_mock):
        signaturit_start_mock.side_effect = self._signaturit_start_side_effect()
        lead_id = self._create_lead()

        with mock.patch.object(
            self.lead_o, 'check_start_signature_process', return_value=('end', '')
        ):
            self.www_lead_o.sign_lead(
                self.cursor, self.uid, lead_id, self._cups,
                context={'skip_validations': True}
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

        with mock.patch.object(
            self.lead_o, 'check_start_signature_process', return_value=('end', '')
        ):
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
