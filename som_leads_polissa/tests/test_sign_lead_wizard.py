# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
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


class TestSignLeadWizard(testing.OOTestCase):

    def setUp(self):
        self.lead_obj = mock.Mock()
        self.process_obj = mock.Mock()
        self.wizard = object.__new__(WizardGenerarLeadPerFirmar)
        self.wizard.pool = _WizardPool(self.lead_obj, self.process_obj)

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

    def test_get_lead_ids_normalizes_context(self):
        self.assertEqual(self.wizard._get_lead_ids(None), [])
        self.assertEqual(
            self.wizard._get_lead_ids({'active_ids': 3}),
            [3],
        )
        self.assertEqual(
            self.wizard._get_lead_ids({'active_ids': [0, 2]}),
            [2],
        )

    def test_signature_without_process(self):
        self._set_signature(1)

        signature = self.wizard._get_signature_data(None, 1, 1, context={})

        self.assertEqual(signature['process_id'], False)
        self.assertIsNone(signature['status'])
        self.assertFalse(self.process_obj.read.called)

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
            self.wizard, None, 1, [1], context={}
        )
        WizardGenerarLeadPerFirmar._replace_signatures(
            self.wizard, None, 1, replaceable, context={}
        )

        self.process_obj.cancel.assert_called_once_with(
            None, 1, [10], context={}
        )
        self.lead_obj.write.assert_called_once()

    def test_action_blocks_completed_signature(self):
        self._set_signature(1, process_id=10, status='completed')
        self.wizard.write = mock.Mock()

        with mock.patch.object(
            WizardGenerarLeadPerFirmar.__bases__[0],
            'action_generar_lead_per_firmar',
            create=True,
        ) as base_action:
            result = self.wizard.action_generar_lead_per_firmar(
                None, 1, [7], context={'active_ids': [1]}
            )

        self.assertTrue(result)
        self.assertFalse(base_action.called)
        self.wizard.write.assert_called_once_with(
            None, 1, [7],
            {
                'state': 'blocked',
                'info': WizardGenerarLeadPerFirmar._COMPLETED_MESSAGE,
            },
            context={'active_ids': [1]},
        )

    def test_action_confirms_active_signature(self):
        self._set_signature(
            1, process_id=10, status='doing', signature_id='remote-10'
        )
        self.wizard.write = mock.Mock()

        with mock.patch.object(
            WizardGenerarLeadPerFirmar.__bases__[0],
            'action_generar_lead_per_firmar',
            create=True,
        ) as base_action:
            result = self.wizard.action_generar_lead_per_firmar(
                None, 1, [7], context={'active_ids': [1]}
            )

        self.assertTrue(result)
        self.assertFalse(base_action.called)
        self.wizard.write.assert_called_once_with(
            None, 1, [7],
            {
                'state': 'confirm',
                'info': WizardGenerarLeadPerFirmar._CONFIRMATION_MESSAGE,
            },
            context={'active_ids': [1]},
        )

    def test_action_returns_success_result_when_wizard_ends(self):
        self._set_signature(1)
        self.wizard.browse = mock.Mock(return_value=mock.Mock(state='end'))

        with mock.patch.object(
            WizardGenerarLeadPerFirmar.__bases__[0],
            'action_generar_lead_per_firmar',
            create=True,
            return_value='base-result',
        ) as base_action:
            result = self.wizard.action_generar_lead_per_firmar(
                None, 1, [7], context={'active_ids': [1]}
            )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(base_action.call_count, 1)

    def test_action_returns_base_result_when_wizard_does_not_end(self):
        self._set_signature(1)
        self.wizard.browse = mock.Mock(return_value=mock.Mock(state='init'))

        with mock.patch.object(
            WizardGenerarLeadPerFirmar.__bases__[0],
            'action_generar_lead_per_firmar',
            create=True,
            return_value='base-result',
        ):
            result = self.wizard.action_generar_lead_per_firmar(
                None, 1, [7], context={'active_ids': [1]}
            )

        self.assertEqual(result, 'base-result')

    def test_confirm_action_blocks_completed_signature(self):
        self._set_signature(1, process_id=10, status='completed')
        self.wizard.write = mock.Mock()

        with mock.patch.object(
            WizardGenerarLeadPerFirmar.__bases__[0],
            'action_generar_lead_per_firmar',
            create=True,
        ) as base_action:
            result = self.wizard.action_confirm_signature_replacement(
                None, 1, [7], context={'active_ids': [1]}
            )

        self.assertTrue(result)
        self.assertFalse(base_action.called)
        self.wizard.write.assert_called_once_with(
            None, 1, [7],
            {
                'state': 'blocked',
                'info': WizardGenerarLeadPerFirmar._COMPLETED_MESSAGE,
            },
            context={'active_ids': [1]},
        )

    def test_confirm_action_returns_success_result(self):
        self._set_signature(1)
        self.wizard.browse = mock.Mock(return_value=mock.Mock(state='end'))

        with mock.patch.object(
            WizardGenerarLeadPerFirmar.__bases__[0],
            'action_generar_lead_per_firmar',
            create=True,
            return_value='base-result',
        ) as base_action:
            result = self.wizard.action_confirm_signature_replacement(
                None, 1, [7], context={'active_ids': [1]}
            )

        self.assertEqual(result['status'], 'success')
        self.assertEqual(base_action.call_count, 1)

    def test_reject_signature_replacement(self):
        self.wizard.write = mock.Mock()

        result = self.wizard.action_reject_signature_replacement(
            None, 1, [7], context={'active_ids': [1]}
        )

        self.assertTrue(result)
        self.wizard.write.assert_called_once_with(
            None, 1, [7], {'state': 'init'}, context={'active_ids': [1]}
        )

    def test_success_result_action(self):
        result = self.wizard._result_action()

        self.assertEqual(result, {
            'type': 'ir.actions.result',
            'status': 'success',
            'title': u'Oferta generada correctament',
            'body': u'L’oferta s’ha generat i està preparada per al procés de firma.',
        })
