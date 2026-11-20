# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class AccountMoveLine(osv.osv):
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


AccountMoveLine()
