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
            raise osv.except_osv(_("Falta dia de pagament!"), _("Els terminis de pagament han de tenir almenys un dia definit."))

    def write(self, cr, uid, ids, vals, context=None):
        super(AccountPaymentTerm, self).write(cr, uid, ids, vals, context=context)
        result = self.browse(cr, uid, id)
        if not result.line_ids:
            raise osv.except_osv(_("Falta dia de pagament!"), _("Els terminis de pagament han de tenir almenys un dia definit."))

AccountPaymentTerm()