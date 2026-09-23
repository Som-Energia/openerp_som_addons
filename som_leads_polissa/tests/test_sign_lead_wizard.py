# -*- coding: utf-8 -*-
from __future__ import absolute_import

from unittest import TestCase

import mock

from som_leads_polissa.wizard.wizard_generar_lead_per_firmar import (
    WizardGenerarLeadPerFirmar,
)


class _WizardPool(object):
    def __init__(self, lead_obj, process_obj):
        self._models = {
            'giscedata.crm.lead': lead_obj,
            'giscedata.signatura.process': process_obj,
        }

    def get(self, model_name):
        return self._models[model_name]


class _WizardProxy(object):
    def __init__(self, lead_obj, process_obj):
        self.pool = _WizardPool(lead_obj, process_obj)


class TestSignLeadWizard(TestCase):

    def setUp(self):
        self.lead_obj = mock.Mock()
        self.process_obj = mock.Mock()
        self.wizard = _WizardProxy(self.lead_obj, self.process_obj)

    def _set_signature(self, lead_id, process_id=False, firmat=False, status=None,
                       signature_id=False):
        self.lead_obj.read.return_value = {
            'signature_process': [process_id, 'Process'] if process_id else False,
            'firmat': firmat,
        }
        self.process_obj.read.return_value = {
            'status': status,
            'signature_id': signature_id,
        }

    def test_delivery_type_selection_and_default(self):
        field = WizardGenerarLeadPerFirmar._columns['delivery_type']
        self.assertEqual(
            field.selection,
            [('poweremail', 'PowerEmail'), ('url', 'No enviar e-mail')]
        )
        self.assertEqual(
            WizardGenerarLeadPerFirmar._defaults['delivery_type'](),
            'poweremail'
        )

    def test_completed_signature_is_blocked(self):
        self._set_signature(1, process_id=10, firmat=False, status='completed')

        blocked, active, replaceable = WizardGenerarLeadPerFirmar._inspect_leads(
            self.wizard, None, 1, [1], context={}
        )

        self.assertEqual([item['lead_id'] for item in blocked], [1])
        self.assertEqual(active, [])
        self.assertEqual(replaceable, [])

    def test_inactive_signature_is_replaceable_without_remote_cancel(self):
        self._set_signature(1, process_id=10, status='canceled')

        blocked, active, replaceable = WizardGenerarLeadPerFirmar._inspect_leads(
            self.wizard, None, 1, [1], context={}
        )
        WizardGenerarLeadPerFirmar._replace_signatures(
            self.wizard, None, 1, replaceable, context={}
        )

        self.assertEqual(blocked, [])
        self.assertEqual(active, [])
        self.assertEqual([item['lead_id'] for item in replaceable], [1])
        self.assertFalse(self.process_obj.cancel.called)
        self.lead_obj.write.assert_called_once_with(
            None, 1, 1,
            {
                'signature_process': False,
                'firmat': False,
                'data_firma': False,
            },
            context={},
        )

    def test_active_signature_is_replaceable_with_remote_cancel(self):
        self._set_signature(
            1, process_id=10, status='doing', signature_id='remote-10'
        )

        _, _, replaceable = WizardGenerarLeadPerFirmar._inspect_leads(
            self.wizard, None, [1], context={}
        )
        WizardGenerarLeadPerFirmar._replace_signatures(
            self.wizard, None, replaceable, context={}
        )

        self.process_obj.cancel.assert_called_once_with(
            None, 1, [10], context={}
        )
        self.lead_obj.write.assert_called_once()

    def test_success_result_action(self):
        result = WizardGenerarLeadPerFirmar._result_action(self.wizard)

        self.assertEqual(result, {
            'type': 'ir.actions.result',
            'status': 'success',
            'title': u'Oferta generada correctament',
            'body': u'L’oferta s’ha generat i està preparada per al procés de firma.',
        })
