# -*- coding: utf-8 -*-
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
