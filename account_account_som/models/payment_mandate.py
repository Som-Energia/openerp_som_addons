# -*- coding: utf-8 -*-
from datetime import datetime

from osv import osv


class PaymentMandate(osv.osv):
    _name = "payment.mandate"
    _inherit = "payment.mandate"

    def get_or_create_payment_mandate(
        self, cursor, uid, partner_id, iban, purpose,
        creditor_code=None, payment_type='recurring', context=None
    ):
        """
        Searches an active payment (SEPA) mandate for
        the partner, iban and purpose (communication).
        If none is found, a new one is created.
        """
        if context is None:
            context = {}

        partner_o = self.pool.get("res.partner")

        partner = partner_o.read(
            cursor, uid, partner_id, ['address', 'name', 'vat'], context=context)
        search_params = [
            ('debtor_iban', '=', iban),
            ('debtor_vat', '=', partner['vat']),
            ('date_end', '=', False),
            ('reference', '=', 'res.partner,{}'.format(partner_id)),
            ('notes', '=', purpose),
        ]

        mandate_ids = self.search(cursor, uid, search_params, context=context)
        if mandate_ids:
            return mandate_ids[0]

        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        mandate_reference = "res.partner,{}".format(partner_id)
        mandate_scheme = "core"

        vals = {
            "date": today,
            "reference": mandate_reference,
            "mandate_scheme": mandate_scheme,
            "signed": 1,
            "debtor_iban": iban.replace(" ", ""),
            "payment_type": payment_type,
            'notes': purpose,
        }

        if creditor_code:
            vals['creditor_code'] = creditor_code

        return self.create(cursor, uid, vals, context=context)


PaymentMandate()
