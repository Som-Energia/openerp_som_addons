# -*- coding: utf-8 -*-
from osv import osv


class PaymentOrder(osv.osv):
    _name = "payment.order"
    _inherit = "payment.order"

    def get_or_create_open_payment_order(
            self, cursor, uid, payment_mode_name, use_invoice=False, context=None):
        """
        Searches an existing payment order (remesa)
        with the proper payment mode and still in draft.
        If none is found, a new one gets created.
        """
        if context is None:
            context = {}

        payment_mode_o = self.pool.get("payment.mode")
        payment_type_o = self.pool.get('payment.type')

        payment_mode_ids = payment_mode_o.search(cursor, uid, [
            ('name', '=', payment_mode_name),
        ], context=context)

        if not payment_mode_ids:
            return False

        payment_orders = self.search(cursor, uid, [
            ('mode', '=', payment_mode_ids[0]),
            ('state', '=', 'draft'),
        ], context=context)
        if payment_orders:
            return payment_orders[0]

        payable_type_id = payment_type_o.search(cursor, uid, [
            ('code', '=', 'TRANSFERENCIA_CSB'),
        ], context=context)[0]

        paymentmode = payment_mode_o.read(cursor, uid, payment_mode_ids[0], context=context)
        order_moves = 'bank-statement' if use_invoice else 'direct-payment'
        order_type = 'payable' if paymentmode['type'][0] == payable_type_id else 'receivable'

        return self.create(cursor, uid, dict(
            date_prefered='fixed',
            user_id=uid,
            state='draft',
            mode=payment_mode_ids[0],
            type=order_type,
            create_account_moves=order_moves,
        ), context=context)


PaymentOrder()
