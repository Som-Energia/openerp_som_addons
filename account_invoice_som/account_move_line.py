# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv
from osv.orm import OnlyFieldsConstraint


class AccountMoveLine(osv.osv):
    _name = "account.move.line"
    _inherit = "account.move.line"

    def _check_different_date_and_period(self, cursor, uid, ids, context={}):
        return_value = True
        am_obj = self.pool.get("account.move")
        if not am_obj._avoid_constraint(cursor, uid, context):
            return_value = super(AccountMoveLine, self)._check_different_date_and_period(
                cursor, uid, ids
            )
        return return_value

    def onchange_account_id(self, cursor, uid, ids, account_id=False, partner_id=False):
        result = super(AccountMoveLine, self).onchange_account_id(
            cursor, uid, ids, account_id, partner_id
        )
        values = result.setdefault("value", {})
        analytic_account_id = values.pop("account_analytic_id", None)
        if analytic_account_id is not None:
            values["analytic_account_id"] = analytic_account_id
        return result

    def onchange_partner_id(
        self,
        cursor,
        uid,
        ids,
        move_id,
        partner_id,
        account_id=None,
        debit=0,
        credit=0,
        date=False,
        journal=False,
    ):
        result = super(AccountMoveLine, self).onchange_partner_id(
            cursor,
            uid,
            ids,
            move_id,
            partner_id,
            account_id,
            debit,
            credit,
            date,
            journal,
        )
        values = result.setdefault("value", {})
        effective_account_id = values.get("account_id") or account_id
        if effective_account_id:
            analytic_result = self.onchange_account_id(
                cursor, uid, ids, effective_account_id, partner_id
            )
            values.update(analytic_result.get("value", {}))
        return result

    _constraints = [
        OnlyFieldsConstraint(
            _check_different_date_and_period,
            "You can not create move line with different period and date",
            ["date", "period_id"],
        )
    ]


AccountMoveLine()


class AccountMove(osv.osv):
    _name = "account.move"
    _inherit = "account.move"

    def _avoid_constraint(self, cursor, uid, context):
        try:
            if context.get("active_id", False) and context.get("som_from_payment_order", False):
                payment_order_obj = self.pool.get("payment.order")
                payment_oder = payment_order_obj.browse(cursor, uid, context.get("active_id"))
                imd_obj = self.pool.get("ir.model.data")
                mode_pagament_socis_id = imd_obj.get_object_reference(
                    cursor, uid, "som_polissa_soci", "mode_pagament_socis"
                )[1]
                return payment_oder.mode.id == mode_pagament_socis_id
        except Exception:
            pass
        return False

    def _check_different_date_and_period(self, cursor, uid, ids, context={}):
        return_value = True
        if not self._avoid_constraint(cursor, uid, context):
            return_value = super(AccountMove, self)._check_different_date_and_period(
                cursor, uid, ids
            )
        return return_value

    _constraints = [
        OnlyFieldsConstraint(
            _check_different_date_and_period,
            "You can not create move line with different period and date",
            ["date", "period_id"],
        )
    ]


AccountMove()
