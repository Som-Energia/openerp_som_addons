# -*- coding: utf-8 -*-
import json

from osv import osv, fields
from tools.translate import _

import generationkwh.investmentmodel as gkwh


class WizardGerneratePaymentMandate(osv.osv_memory):
    _name = 'wizard.generate.payment.mandate'

    def _default_partner_id(self, cursor, uid, context=None):
        id_partner = False
        if context:
            id_partner = context.get('active_id', False)
        return id_partner

    def action_generate_mandate(self, cursor, uid, ids, context=None):

        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0], context)
        GenerationkwhInvestment = self.pool.get('generationkwh.investment')
        id_mandate = GenerationkwhInvestment.get_or_create_payment_mandate(cursor, uid,
                wiz.partner_id.id,
                wiz.bank_id.iban,
                gkwh.mandatePurposeAmorCobrar,
                gkwh.creditorCode
            )

        self.write(cursor, uid, ids, {
            'state': 'done',
            'mandate_id': id_mandate,
        })
        return True

    _columns = {
        'partner_id': fields.many2one(
            'res.partner', 'Client',
            required=True, ondelete='cascade', readonly=True,
        ),
        'bank_id': fields.many2one('res.partner.bank', 'Banc client', required=True, ondelete='cascade'),
        'mandate_id': fields.many2one('payment.mandate', 'Mandat', required=False),
        'state': fields.char('State', size=16),
    }

    _defaults = {
        'partner_id': _default_partner_id,
        'state': lambda *a: 'init',
    }


WizardGerneratePaymentMandate()
