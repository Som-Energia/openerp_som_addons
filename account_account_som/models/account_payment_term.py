# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _


class AccountPaymentTerm(osv.osv):
    _name = "account.payment.term"
    _inherit = "account.payment.term"

    def create(self, cr, uid, vals, context={}):
        id = super(AccountPaymentTerm, self).create(cr, uid, vals, context=context)
        result = self.browse(cr, uid, id)
        if not result.line_ids:
            raise osv.except_osv(
                _("Falta dia de pagament!"),
                _("Els terminis de pagament han de tenir almenys un dia definit."),
            )
        return id

    def write(self, cr, uid, ids, vals, context=None):
        super(AccountPaymentTerm, self).write(cr, uid, ids, vals, context=context)
        for _id in ids:
            result = self.browse(cr, uid, _id)
            if not result.line_ids:
                raise osv.except_osv(
                    _("Falta dia de pagament!"),
                    _("Els terminis de pagament han de tenir almenys un dia definit."),
                )
        return True


AccountPaymentTerm()


class AccountPaymentTermLine(osv.osv):
    _name = "account.payment.term.line"
    _inherit = "account.payment.term.line"

    _columns = {
        "payment_id": fields.many2one(
            "account.payment.term", "Payment Term", required=True, select=True, ondelete="cascade"
        ),
    }

    _defaults = {
        "days": lambda *a: 0,
    }


AccountPaymentTermLine()
