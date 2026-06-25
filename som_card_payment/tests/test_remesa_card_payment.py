# -*- coding: utf-8 -*-

from destral import testing
from osv import osv


class TestCardPaymentNotInRemesa(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestCardPaymentNotInRemesa, self).setUp()
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.invoice_obj = self.openerp.pool.get("account.invoice")
        self.payment_order_obj = self.openerp.pool.get("payment.order")

        self.card_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        self.demo_mode_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "account_payment", "payment_mode_demo"
        )[1]
        demo_mode_name = self.openerp.pool.get("payment.mode").read(
            self.cursor, self.uid, self.demo_mode_id, ["name"]
        )["name"]
        self.order_id = self.payment_order_obj.get_or_create_open_payment_order(
            self.cursor, self.uid, demo_mode_name
        )

    def _get_open_invoice_ids(self, limit=2):
        return self.invoice_obj.search(
            self.cursor,
            self.uid,
            [
                ("type", "=", "out_invoice"),
                ("state", "in", ["open", "draft"]),
                ("payment_order_id", "=", False),
            ],
            limit=limit,
        )

    def test_add_to_remesa_raises_for_card_recurrent_invoice(self):
        invoice_ids = self._get_open_invoice_ids(limit=1)
        if not invoice_ids:
            self.skipTest("No hi ha factures obertes disponibles per provar la remesa")
        invoice_id = invoice_ids[0]

        self.invoice_obj.write(
            self.cursor,
            self.uid,
            [invoice_id],
            {"payment_type": self.card_type_id},
        )

        with self.assertRaises(osv.except_osv):
            self.invoice_obj.afegeix_a_remesa(
                self.cursor, self.uid, [invoice_id], self.order_id
            )

        inv = self.invoice_obj.read(self.cursor, self.uid, invoice_id, ["payment_order_id"])
        self.assertFalse(inv["payment_order_id"])

    def test_add_to_remesa_is_atomic_when_mixed_invoices(self):
        invoice_ids = self._get_open_invoice_ids(limit=2)
        if len(invoice_ids) < 2:
            self.skipTest("No hi ha suficients factures obertes per provar la remesa mixta")

        card_invoice_id = invoice_ids[0]
        normal_invoice_id = invoice_ids[1]

        self.invoice_obj.write(
            self.cursor,
            self.uid,
            [card_invoice_id],
            {"payment_type": self.card_type_id},
        )

        with self.assertRaises(osv.except_osv):
            self.invoice_obj.afegeix_a_remesa(
                self.cursor,
                self.uid,
                [card_invoice_id, normal_invoice_id],
                self.order_id,
            )

        invoices = self.invoice_obj.read(
            self.cursor,
            self.uid,
            [card_invoice_id, normal_invoice_id],
            ["payment_order_id"],
        )
        for inv in invoices:
            self.assertFalse(inv["payment_order_id"])

    def test_add_to_remesa_async_raises_for_card_recurrent_invoice(self):
        if not hasattr(self.invoice_obj, "afegeix_a_remesa_async"):
            self.skipTest("No hi ha afegeix_a_remesa_async disponible en aquest entorn")

        invoice_ids = self._get_open_invoice_ids(limit=1)
        if not invoice_ids:
            self.skipTest("No hi ha factures obertes disponibles per provar la remesa")
        invoice_id = invoice_ids[0]

        self.invoice_obj.write(
            self.cursor,
            self.uid,
            [invoice_id],
            {"payment_type": self.card_type_id},
        )

        with self.assertRaises(osv.except_osv):
            self.invoice_obj.afegeix_a_remesa_async(
                self.cursor, self.uid, [invoice_id], self.order_id
            )

        inv = self.invoice_obj.read(self.cursor, self.uid, invoice_id, ["payment_order_id"])
        self.assertFalse(inv["payment_order_id"])
