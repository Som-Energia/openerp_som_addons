# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction
from mock import Mock, patch


class TestSomWebformsHelpersPolissa(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.helper_obj = self.openerp.pool.get("som.polissa.webforms.helpers")
        self.imd_obj = self.openerp.pool.get("ir.model.data")

    def tearDown(self):
        self.txn.stop()

    def _open_polissa(self, xml_ref):
        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa", xml_ref
        )[1]

        self.polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])

        return polissa_id

    def test_www_get_iban(self):
        polissa_id = self._open_polissa("polissa_domestica_0100")
        result = self.helper_obj.www_get_iban(self.cursor, self.uid, polissa_id)
        self.assertEqual(result, "**** **** **** **** **** 9397")

    def test_www_check_iban(self):
        correct_iban = "ES3120170806126133002095"
        incorrect_iban = "ES2222170806122222222222"
        result = self.helper_obj.www_check_iban(self.cursor, self.uid, correct_iban)
        self.assertEqual(result, correct_iban)
        result = self.helper_obj.www_check_iban(self.cursor, self.uid, incorrect_iban)
        self.assertEqual(result, False)

    def test_www_set_iban(self):
        polissa_id = self._open_polissa("polissa_domestica_0100")
        new_iban = "ES31 2017 0806 1261 3300 2095"
        self.helper_obj.www_set_iban(self.cursor, self.uid, polissa_id, new_iban)
        new_iban_pol = self.polissa_obj.read(self.cursor, self.uid, polissa_id, ["bank"])["bank"][1]
        self.assertEqual(new_iban_pol, new_iban)

    def _payment_lines_pool(self, order_state="draft", with_move=True):
        factura = Mock()
        factura.payment_order_id.id = 10
        factura.payment_order_id.state = order_state
        factura.move_id = Mock() if with_move else False
        if with_move:
            factura.move_id.line_id = [Mock(id=101), Mock(id=102)]

        pool = Mock()
        fact_obj = Mock()
        fact_obj.search.return_value = [1]
        fact_obj.browse.return_value = [factura]
        pol_obj = Mock()
        pol_obj.read.return_value = {"bank": [999, "New bank"], "titular": [20, "Holder"]}
        line_obj = Mock()
        pool.get.side_effect = {
            "giscedata.facturacio.factura": fact_obj,
            "giscedata.polissa": pol_obj,
            "payment.line": line_obj,
        }.get
        return pool, fact_obj, line_obj

    def test_update_payment_lines_only_selected_contract(self):
        pool, fact_obj, line_obj = self._payment_lines_pool()
        lines = [
            {"id": 1, "order_id": 10, "partner_id": 20, "move_line_id": 101, "bank_id": 111},
            {"id": 2, "order_id": 10, "partner_id": 20, "move_line_id": 201, "bank_id": 222},
            {"id": 3, "order_id": 10, "partner_id": 20, "move_line_id": 102, "bank_id": 111},
            {"id": 4, "order_id": 11, "partner_id": 20, "move_line_id": 101, "bank_id": 444},
            {"id": 5, "order_id": 10, "partner_id": 21, "move_line_id": 101, "bank_id": 555},
        ]

        def search(cursor, uid, domain):
            return [
                line["id"] for line in lines
                if all(
                    line[field] in value if operator == "in" else line[field] == value
                    for field, operator, value in domain
                )
            ]

        def write(cursor, uid, ids, values):
            for line in lines:
                if line["id"] in ids:
                    line.update(values)

        line_obj.search.side_effect = search
        line_obj.write.side_effect = write
        with patch.object(self.helper_obj, "pool", pool):
            self.helper_obj._update_payment_lines(self.cursor, self.uid, 1, {})

        fact_obj.search.assert_called_once_with(
            self.cursor, self.uid,
            [
                ("polissa_id", "=", 1),
                ("type", "in", ["out_invoice", "out_refund"]),
                ("state", "in", ["draft", "open"]),
            ],
            context={},
        )
        self.assertEqual([line["bank_id"] for line in lines], [999, 222, 999, 444, 555])

    def test_update_payment_lines_ignores_non_draft_order(self):
        pool, _, line_obj = self._payment_lines_pool(order_state="done")
        with patch.object(self.helper_obj, "pool", pool):
            self.helper_obj._update_payment_lines(self.cursor, self.uid, 1, {})
        line_obj.search.assert_not_called()
        line_obj.write.assert_not_called()

    def test_update_payment_lines_without_accounting_move(self):
        pool, _, line_obj = self._payment_lines_pool(with_move=False)
        with patch.object(self.helper_obj, "pool", pool):
            self.helper_obj._update_payment_lines(self.cursor, self.uid, 1, {})
        line_obj.search.assert_not_called()
        line_obj.write.assert_not_called()
