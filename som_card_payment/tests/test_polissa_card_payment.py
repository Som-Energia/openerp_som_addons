# -*- coding: utf-8 -*-

from destral import testing
from osv.orm import FieldsValidationException


class TestCardPaymentInPolissa(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestCardPaymentInPolissa, self).setUp()
        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.card_obj = self.openerp.pool.get("res.partner.creditcard")
        self.imd_obj = self.openerp.pool.get("ir.model.data")

        try:
            self.polissa_id = self.imd_obj.get_object_reference(
                self.cursor, self.uid, "som_polissa", "polissa_domestica_0100"
            )[1]
        except Exception:
            polissa_ids = self.polissa_obj.search(self.cursor, self.uid, [], limit=1)
            if not polissa_ids:
                self.skipTest("No hi ha cap polissa disponible per provar modcontractual")
            self.polissa_id = polissa_ids[0]
        self.payment_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        self.payment_mode_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_mode_card_recurrent"
        )[1]

    def test_modcon_to_card_payment_mode_requires_creditcard(self):
        self.polissa_obj.send_signal(self.cursor, self.uid, [self.polissa_id], ["modcontractual"])
        with self.assertRaises(FieldsValidationException):
            self.polissa_obj.write(
                self.cursor,
                self.uid,
                [self.polissa_id],
                {
                    "payment_mode_id": self.payment_mode_id,
                    "tipo_pago": self.payment_type_id,
                    "creditcard": False,
                },
            )

    def test_modcon_to_card_payment_mode_with_creditcard(self):
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)
        card_id = self.card_obj.create(
            self.cursor,
            self.uid,
            {
                "partner_id": polissa.pagador.id,
                "token": "tok_polissa_1",
                "expiry_date": "12/35",
                "masked_number": "**** **** **** 1111",
            },
        )

        self.polissa_obj.send_signal(self.cursor, self.uid, [self.polissa_id], ["modcontractual"])
        self.polissa_obj.write(
            self.cursor,
            self.uid,
            [self.polissa_id],
            {
                "payment_mode_id": self.payment_mode_id,
                "tipo_pago": self.payment_type_id,
                "creditcard": card_id,
            },
        )
        values = self.polissa_obj.read(
            self.cursor,
            self.uid,
            self.polissa_id,
            ["payment_mode_id", "tipo_pago", "creditcard"],
        )
        self.assertEqual(values["payment_mode_id"][0], self.payment_mode_id)
        self.assertEqual(values["tipo_pago"][0], self.payment_type_id)
        self.assertEqual(values["creditcard"][0], card_id)
