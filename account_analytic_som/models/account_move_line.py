# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class AccountMoveLine(osv.osv):
    _name = "account.move.line"
    _inherit = "account.move.line"

    def onchange_account_id(
        self, cursor, uid, ids, account_id=False, partner_id=False
    ):
        result = super(AccountMoveLine, self).onchange_account_id(
            cursor, uid, ids, account_id, partner_id
        )
        values = result["value"]
        # Older analytic defaults return the invoice-line field name.
        if "account_analytic_id" in values:
            analytic_id = values.pop("account_analytic_id")
            values.setdefault("analytic_account_id", analytic_id)
        return result

    def get_default_analytic_account(self, cursor, uid, line_id, context=None):
        """Resolve the default using the entry line's accounting date."""
        line = self.browse(cursor, uid, line_id, context=context)
        rule = self.pool.get("account.analytic.default").account_get(
            cursor, uid, account_id=line.account_id.id,
            partner_id=line.partner_id.id, product_id=line.product_id.id,
            user_id=uid, date=line.date, context=context,
        )
        return rule.analytic_id.id if rule and rule.analytic_id else False


AccountMoveLine()
