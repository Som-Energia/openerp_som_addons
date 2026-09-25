# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv, fields
from tools.translate import _


class WizardGenerarLeadPerFirmar(osv.osv_memory):
    _inherit = 'wizard.generar.lead.per.firmar'

    _INACTIVE_SIGNATURE_STATUSES = (
        'canceled', 'error', 'declined', 'unsend', 'expired'
    )
    _CONFIRMATION_MESSAGE = _(
        u'Aquest lead ja té una firma digital, vols cancelar-la i generar una de nova?'
    )
    _COMPLETED_MESSAGE = _(
        u'La firma està completada. Cal desvincular o eliminar la firma del lead manualment.'
    )

    def _get_lead_ids(self, context):
        lead_ids = (context or {}).get('active_ids', [])
        if not isinstance(lead_ids, (list, tuple)):
            lead_ids = [lead_ids]
        return [lead_id for lead_id in lead_ids if lead_id]

    def _get_signature_data(self, cursor, uid, lead_id, context=None):
        lead_obj = self.pool.get('giscedata.crm.lead')
        process_obj = self.pool.get('giscedata.signatura.process')
        lead_data = lead_obj.read(
            cursor, uid, lead_id, ['signature_process', 'firmat'], context=context
        )
        process = lead_data.get('signature_process')
        process_id = process[0] if isinstance(process, (list, tuple)) else process
        process_data = {}
        if process_id:
            process_data = process_obj.read(
                cursor, uid, process_id, ['status', 'signature_id'], context=context
            ) or {}
        return {
            'lead_id': lead_id,
            'process_id': process_id,
            'firmat': bool(lead_data.get('firmat')),
            'status': process_data.get('status'),
            'signature_id': process_data.get('signature_id'),
        }

    def _inspect_leads(self, cursor, uid, lead_ids, context=None):
        signatures = [
            self._get_signature_data(cursor, uid, lead_id, context=context)
            for lead_id in lead_ids
        ]
        blocked = [
            signature for signature in signatures
            if signature['firmat'] or signature['status'] == 'completed'
        ]
        active = [
            signature for signature in signatures
            if signature['process_id'] and signature not in blocked
            and signature['status'] not in self._INACTIVE_SIGNATURE_STATUSES
        ]
        replaceable = [
            signature for signature in signatures
            if signature['process_id'] and signature not in blocked
        ]
        return blocked, active, replaceable

    def _clean_signature_link(self, cursor, uid, lead_id, context=None):
        lead_obj = self.pool.get('giscedata.crm.lead')
        lead_obj.write(
            cursor, uid, lead_id,
            {
                'signature_process': False,
                'firmat': False,
                'data_firma': False,
            },
            context=context,
        )

    def _replace_signatures(self, cursor, uid, signatures, context=None):
        process_obj = self.pool.get('giscedata.signatura.process')
        for signature in signatures:
            if signature['status'] not in self._INACTIVE_SIGNATURE_STATUSES:
                if signature['signature_id']:
                    process_obj.cancel(
                        cursor, uid, [signature['process_id']], context=context
                    )
            self._clean_signature_link(
                cursor, uid, signature['lead_id'], context=context
            )

    def _set_state(self, cursor, uid, wizard_id, state, info, context=None):
        self.write(
            cursor, uid, [wizard_id],
            {'state': state, 'info': info},
            context=context,
        )

    def _result_action(self):
        return {
            'type': 'ir.actions.result',
            'status': 'success',
            'title': _('Oferta generada correctament'),
            'body': _(
                u'L’oferta s’ha generat i està preparada per al procés de firma.'
            ),
        }

    def action_generar_lead_per_firmar(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        wizard_id = ids[0]
        lead_ids = self._get_lead_ids(context)
        if not lead_ids:
            raise osv.except_osv(
                _('Error'), _('No s\'ha seleccionat cap registre')
            )

        blocked, active, replaceable = self._inspect_leads(
            cursor, uid, lead_ids, context=context
        )
        if blocked:
            self._set_state(
                cursor, uid, wizard_id, 'blocked', self._COMPLETED_MESSAGE,
                context=context,
            )
            return True
        if active:
            self._set_state(
                cursor, uid, wizard_id, 'confirm', self._CONFIRMATION_MESSAGE,
                context=context,
            )
            return True
        if replaceable:
            self._replace_signatures(
                cursor, uid, replaceable, context=context
            )

        result = super(
            WizardGenerarLeadPerFirmar, self
        ).action_generar_lead_per_firmar(
            cursor, uid, ids, context=context
        )
        wizard = self.browse(cursor, uid, wizard_id, context=context)
        if wizard.state == 'end':
            return self._result_action()
        return result

    def action_confirm_signature_replacement(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        wizard_id = ids[0]
        lead_ids = self._get_lead_ids(context)
        if not lead_ids:
            raise osv.except_osv(
                _('Error'), _('No s\'ha seleccionat cap registre')
            )

        inspection = self._inspect_leads(
            cursor, uid, lead_ids, context=context
        )
        blocked = inspection[0]
        replaceable = inspection[2]
        if blocked:
            self._set_state(
                cursor, uid, wizard_id, 'blocked', self._COMPLETED_MESSAGE,
                context=context,
            )
            return True

        self._replace_signatures(
            cursor, uid, replaceable, context=context
        )
        result = super(
            WizardGenerarLeadPerFirmar, self
        ).action_generar_lead_per_firmar(
            cursor, uid, ids, context=context
        )
        wizard = self.browse(cursor, uid, wizard_id, context=context)
        if wizard.state == 'end':
            return self._result_action()
        return result

    def action_reject_signature_replacement(self, cursor, uid, ids, context=None):
        self.write(
            cursor, uid, [ids[0]], {'state': 'init'}, context=context
        )
        return True

    _columns = {
        'delivery_type': fields.selection(
            [('poweremail', 'PowerEmail'), ('url', 'No enviar e-mail')],
            'Tipo envio'
        ),
        'state': fields.selection([
            ('init', 'Inicial'),
            ('confirm', 'Confirmació'),
            ('blocked', 'Bloquejat'),
            ('end', 'Final'),
            ('error', 'Error'),
        ], 'Estado'),
    }

    _defaults = {
        'delivery_type': lambda *a: 'poweremail',
    }


WizardGenerarLeadPerFirmar()
