# -*- coding: utf-8 -*-

from destral import testing
from osv.orm import FieldsValidationException


class TestResPartnerCreditCard(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestResPartnerCreditCard, self).setUp()
        self.partner_obj = self.openerp.pool.get("res.partner")
        self.creditcard_obj = self.openerp.pool.get("res.partner.creditcard")
        self.partner_id = self.partner_obj.create(
            self.cursor,
            self.uid,
            {"name": "Partner test card payment"},
        )

    def _base_vals(self):
        return {
            "partner_id": self.partner_id,
            "token": "tok_test_123",
            "masked_number": "**** **** **** 1234",
        }

    def test_check_expiry_date_accepts_valid_format(self):
        vals = self._base_vals()
        vals["expiry_date"] = "12/34"

        card_id = self.creditcard_obj.create(self.cursor, self.uid, vals)
        self.assertTrue(card_id)

    def test_check_expiry_date_rejects_invalid_month(self):
        vals = self._base_vals()
        vals["expiry_date"] = "13/24"

        with self.assertRaises(FieldsValidationException):
            self.creditcard_obj.create(self.cursor, self.uid, vals)

    def test_check_expiry_date_rejects_invalid_write_format(self):
        vals = self._base_vals()
        vals["expiry_date"] = "01/24"
        card_id = self.creditcard_obj.create(self.cursor, self.uid, vals)

        with self.assertRaises(FieldsValidationException):
            self.creditcard_obj.write(
                self.cursor,
                self.uid,
                [card_id],
                {"expiry_date": "1/24"},
            )


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
