# -*- coding: utf-8 -*-

from osv import osv


class PaymentLine(osv.osv):
    _name = "payment.line"
    _inherit = "payment.line"

    def onchange_move_line(
        self,
        cr,
        uid,
        ids,
        move_line_id,
        payment_type,
        date_prefered,
        date_planned,
        currency=False,
        company_currency=False,
        context=None,
    ):
        # Adds account.move.line name to the payment line communication
        res = super(PaymentLine, self).onchange_move_line(
            cr,
            uid,
            ids,
            move_line_id,
            payment_type,
            date_prefered,
            date_planned,
            currency,
            company_currency,
            context,
        )
        if move_line_id:
            line = self.pool.get("account.move.line").browse(cr, uid, move_line_id)
            if line.name != "/":
                res["value"]["communication"] = (
                    str(res["value"]["communication"]) + ". " + str(line.name)
                )
            res["value"]["account_id"] = line.account_id.id
        return res


PaymentLine()
