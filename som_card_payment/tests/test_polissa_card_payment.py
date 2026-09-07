# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from datetime import date
from osv.orm import FieldsValidationException


class TestCardPaymentInPolissa(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestCardPaymentInPolissa, self).setUp()
        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.modcontractual_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        self.card_obj = self.openerp.pool.get("res.partner.creditcard")
        self.payment_type_obj = self.openerp.pool.get("payment.type")
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

    def _get_modcontractual_id_for_validation(self):
        self._ensure_modcontractual_for_polissa()

        modcontractual_ids = self.modcontractual_obj.search(
            self.cursor,
            self.uid,
            [("polissa_id", "=", self.polissa_id), ("active", "=", True)],
            limit=1,
            order="id desc",
        )
        if not modcontractual_ids:
            self.fail("No hi ha cap modcontractual per provar validacions")
        return modcontractual_ids[0]

    def _ensure_modcontractual_for_polissa(self):
        modcontractual_ids = self.modcontractual_obj.search(
            self.cursor,
            self.uid,
            [("polissa_id", "=", self.polissa_id)],
            limit=1,
        )
        if modcontractual_ids:
            return

        self.polissa_obj.send_signal(
            self.cursor,
            self.uid,
            [self.polissa_id],
            ["validar", "contracte", "modcontractual"],
        )

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

    def test_activation_keeps_card_payment_data(self):
        polissa = self.polissa_obj.browse(
            self.cursor, self.uid, self.polissa_id
        )
        card_id = self.card_obj.create(
            self.cursor,
            self.uid,
            {
                "partner_id": polissa.pagador.id,
                "token": "tok_activation_1",
                "expiry_date": "12/35",
                "masked_number": "**** **** **** 2222",
            },
        )
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

        self.polissa_obj.wkf_activa(
            self.cursor, self.uid, [self.polissa_id]
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

    def test_copy_data_replaces_card_payment_data(self):
        polissa = self.polissa_obj.browse(
            self.cursor, self.uid, self.polissa_id
        )
        card_id = self.card_obj.create(
            self.cursor,
            self.uid,
            {
                "partner_id": polissa.pagador.id,
                "token": "tok_copy_1",
                "expiry_date": "12/35",
                "masked_number": "**** **** **** 2222",
            },
        )
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

        copy_values = self.polissa_obj.copy_data(
            self.cursor, self.uid, self.polissa_id
        )[0]
        payment_mode_obj = self.openerp.pool.get("payment.mode")
        enginyers_mode_id = payment_mode_obj.search(
            self.cursor, self.uid, [("name", "=", "ENGINYERS")], limit=1
        )[0]
        enginyers_mode = payment_mode_obj.browse(
            self.cursor, self.uid, enginyers_mode_id
        )

        self.assertEqual(copy_values["payment_mode_id"], enginyers_mode_id)
        self.assertEqual(copy_values["tipo_pago"], enginyers_mode.type.id)
        self.assertFalse(copy_values["creditcard"])

    def test_onchange_tipo_pago_clears_creditcard_for_non_recurrent(self):
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)
        non_recurrent_type_ids = self.payment_type_obj.search(
            self.cursor,
            self.uid,
            [("code", "!=", "COBRAMENT_RECURRENT_TARGETA")],
            limit=1,
        )
        if not non_recurrent_type_ids:
            self.skipTest("No hi ha tipus de pagament no recurrent per provar")
        non_recurrent_type_id = non_recurrent_type_ids[0]

        non_recurrent_values = self.polissa_obj.onchange_tipo_pago(
            self.cursor,
            self.uid,
            [self.polissa_id],
            non_recurrent_type_id,
            polissa.pagador.id,
        )
        self.assertEqual(non_recurrent_values["value"]["creditcard"], False)

        empty_type_values = self.polissa_obj.onchange_tipo_pago(
            self.cursor,
            self.uid,
            [self.polissa_id],
            False,
            polissa.pagador.id,
        )
        self.assertEqual(empty_type_values["value"]["creditcard"], False)

    def test_modcontractual_requires_creditcard_from_pagador(self):
        modcontractual_id = self._get_modcontractual_id_for_validation()
        self.payment_type_obj.write(
            self.cursor,
            self.uid,
            [self.payment_type_id],
            {"code": "COBRAMENT_RECURRENT_TARGETA"},
        )

        other_partner_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_2"
        )[1]
        invalid_card_id = self.card_obj.create(
            self.cursor,
            self.uid,
            {
                "partner_id": other_partner_id,
                "token": "tok_other_partner",
                "expiry_date": "10/35",
                "masked_number": "**** **** **** 3333",
            },
        )

        with self.assertRaises(FieldsValidationException):
            self.modcontractual_obj.write(
                self.cursor,
                self.uid,
                [modcontractual_id],
                {
                    "tipo_pago": self.payment_type_id,
                    "payment_mode_id": self.payment_mode_id,
                    "creditcard": invalid_card_id,
                },
            )

    def test_convert_to_recurring_card_returns_noop_for_equivalent_card(self):
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)
        card_id = self.card_obj.create(
            self.cursor,
            self.uid,
            {
                "partner_id": polissa.pagador.id,
                "token": "tok_convert_noop",
                "cof_txnid": "cof_convert_noop",
                "expiry_date": "12/35",
                "masked_number": "**** **** **** 4242",
            },
        )
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

        result = self.polissa_obj.convert_to_recurring_card(
            self.cursor,
            self.uid,
            self.polissa_id,
            {
                "token": "tok_convert_noop",
                "cof_txnid": "cof_convert_noop",
                "expiry_date": "12/35",
                "masked_number": "**** **** **** 4242",
            },
        )

        self.assertEqual(result["status"], "no-op")
        self.assertEqual(result["reason_code"], "already_converted")
        self.assertEqual(result["card"]["id"], card_id)
        self.assertEqual(result["policy"]["effective_date"], date.today().strftime("%Y-%m-%d"))

    def test_convert_to_recurring_card_creates_today_modification(self):
        self._ensure_modcontractual_for_polissa()
        self.polissa_obj.wkf_activa(self.cursor, self.uid, [self.polissa_id])
        polissa_id = self.polissa_id
        card_data = {
            "token": "tok_convert_today",
            "cof_txnid": "cof_convert_today",
            "expiry_date": "12/35",
            "masked_number": "**** **** **** 4243",
        }

        result = self.polissa_obj.convert_to_recurring_card(
            self.cursor, self.uid, polissa_id, card_data
        )

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["card"]["disposition"], "created")
        self.assertEqual(result["policy"], {
            "id": polissa_id,
            "disposition": "updated",
            "effective_date": date.today().strftime("%Y-%m-%d"),
        })
        polissa = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(polissa.creditcard.id, result["card"]["id"])
        self.assertEqual(polissa.tipo_pago.id, self.payment_type_id)
        self.assertEqual(polissa.payment_mode_id.id, self.payment_mode_id)

    def test_recurring_card_result_is_partial_for_remitted_noop_policy(self):
        result = self.polissa_obj._recurring_card_result(
            {"id": 10, "disposition": "reused"},
            {"id": 11, "disposition": "unchanged", "effective_date": "2026-09-07"},
            {"migrated": [], "remitted": [12], "failed": [], "unchanged": []},
            "2026-09-07",
        )

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["reason_code"], "invoice_excluded_or_failed")
