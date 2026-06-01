# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv
from tools.translate import _


class AccountInvoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"

    def afegeix_a_remesa(self, cursor, uid, ids, order_id, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        blocked_invoice_names = []
        for invoice in self.browse(cursor, uid, ids, context=context):
            payment_type = getattr(invoice, "payment_type", False)
            if payment_type and payment_type.code == "COBRAMENT_RECURRENT_TARGETA":
                blocked_invoice_names.append(invoice.number or str(invoice.id))

        if blocked_invoice_names:
            raise osv.except_osv(
                _("Error"),
                _(
                    "No es poden afegir a una remesa les factures amb "
                    "cobrament recurrent per targeta. "
                    "Factures afectades: %s"
                )
                % ", ".join(blocked_invoice_names),
            )

        return super(AccountInvoice, self).afegeix_a_remesa(
            cursor, uid, ids, order_id, context=context
        )


AccountInvoice()
