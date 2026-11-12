# -*- coding: utf-8 -*-
from yamlns import namespace as ns

from destral import testing
from destral.transaction import Transaction


class TestPaymentOrderSom(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.payment_order_o = self.model("payment.order")
        self.payment_mode_o = self.model("payment.mode")

        self.imd_obj = self.model('ir.model.data')
        payment_mode_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "account_payment", "payment_mode_demo"
        )[1]

        self.payment_mode = self.payment_mode_o.browse(
            self.cursor, self.uid, payment_mode_id)

    def tearDown(self):
        self.txn.stop()

    from .utils import assertNsEqual  # legacy gkwh method of abstacting this method

    def test_get_or_create_payment_order_bad_name(self):
        order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, "BAD MODE")
        self.assertEqual(order_id, False)

    def test_get_or_create_payment_order_called_twice_returns_the_same(self):
        first_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name)
        second_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name)
        self.assertEqual(first_order_id, second_order_id)

    def test_get_or_create_payment_order_no_draft_creates_a_new_one(self):
        first_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name)
        self.payment_order_o.write(self.cursor, self.uid, first_order_id, dict(
            state='done',
        ))
        second_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name)
        self.assertNotEqual(first_order_id, second_order_id)

    def test_get_or_create_payment_order_proper_fields_set(self):
        first_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name)
        self.payment_order_o.write(self.cursor, self.uid, first_order_id, dict(
            state='done',
        ))

        second_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name)
        order = ns(self.payment_order_o.read(self.cursor, self.uid, second_order_id, [
            "date_prefered",
            "user_id",
            "state",
            "mode",
            "type",
            "create_account_moves",
        ]))
        order.user_id = order.user_id[0]
        order.mode = order.mode[1]
        self.assertNsEqual(order, """\
             id: {}
             create_account_moves: direct-payment
             date_prefered: fixed
             mode: Pay Demo Mode
             state: draft
             type: receivable
             user_id: {}
            """.format(
            second_order_id,
            order.user_id,
        ))

    def test_get_or_create_payment_order_receivable_invoice(self):
        previous_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name)
        self.payment_order_o.write(self.cursor, self.uid, previous_order_id, dict(
            state='done',
        ))

        order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid,
            self.payment_mode.name,
            use_invoice=True,
        )

        order = self.payment_order_o.read(
            self.cursor, self.uid, order_id, ['create_account_moves', 'type'])
        order.pop('id')
        self.assertNsEqual(order, """\
                create_account_moves: bank-statement
                type: receivable
                """)

    def test_get_or_create_payment_order_payable_invoice(self):
        payment_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "l10n_ES_remesas", "payment_type_transferencia0"
        )[1]
        self.payment_mode_o.write(
            self.cursor, self.uid, self.payment_mode.id, {"type": payment_type_id, "tipo": "sepa34"}
        )

        previous_order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name
        )
        self.payment_order_o.write(
            self.cursor, self.uid, previous_order_id, dict(state='done')
        )

        order_id = self.payment_order_o.get_or_create_open_payment_order(
            self.cursor, self.uid, self.payment_mode.name, use_invoice=True,
        )

        order = self.payment_order_o.read(
            self.cursor, self.uid, order_id, ['create_account_moves', 'type']
        )
        order.pop('id')
        self.assertNsEqual(order, """\
                create_account_moves: bank-statement
                type: payable
                """)
