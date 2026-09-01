# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date, timedelta
import time

from destral import testing
import mock
from osv import osv


class TestRedsysCardCollection(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRedsysCardCollection, self).setUp()
        self.config_obj = self.openerp.pool.get("res.config")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.invoice_obj = self.openerp.pool.get("account.invoice")
        self.factura_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        self.card_obj = self.openerp.pool.get("res.partner.creditcard")
        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.account_obj = self.openerp.pool.get("account.account")

        self.card_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        self._configure_redsys()

    def _configure_redsys(self):
        payment_mode_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_mode_card_recurrent"
        )[1]
        payment_mode = self.openerp.pool.get("payment.mode").browse(
            self.cursor, self.uid, payment_mode_id
        )
        self.config_obj.set(self.cursor, self.uid, "redsys_merchant_code", "999008881")
        self.config_obj.set(self.cursor, self.uid, "redsys_private_key", "secret")
        self.config_obj.set(
            self.cursor, self.uid, "redsys_merchant_url", "https://merchant.local/notify"
        )
        self.config_obj.set(self.cursor, self.uid, "redsys_terminal", "1")
        self.config_obj.set(self.cursor, self.uid, "redsys_currency", "978")
        self.config_obj.set(self.cursor, self.uid, "redsys_timeout", "30")
        self.config_obj.set(
            self.cursor, self.uid, "redsys_tpv_journal_id", str(payment_mode.journal.id)
        )
        self.config_obj.set(
            self.cursor,
            self.uid,
            "redsys_tpv_pay_account_id",
            str(payment_mode.journal.default_credit_account_id.id),
        )

    def test_redsys_config_data_has_safe_defaults(self):
        expected_values = {
            "redsys_merchant_code": "DEMO_MERCHANT_CODE",
            "redsys_private_key": "DEMO_PRIVATE_KEY",
            "redsys_merchant_url": "https://example.invalid/redsys",
            "redsys_endpoint_url": "https://sis.redsys.es/sis/rest/trataPeticionREST",
            "redsys_terminal": "1",
            "redsys_currency": "978",
            "redsys_timeout": "30",
        }

        for key, expected_value in expected_values.items():
            config_id = self.imd_obj.get_object_reference(
                self.cursor, self.uid, "som_card_payment", key
            )[1]
            config = self.config_obj.browse(self.cursor, self.uid, config_id)
            self.assertEqual(config.name, key)
            self.assertEqual(config.value, expected_value)

    def test_get_redsys_config_uses_default_timeout_when_invalid(self):
        self.config_obj.set(self.cursor, self.uid, "redsys_timeout", "invalid")

        config = self.factura_obj._get_redsys_config(self.cursor, self.uid)

        self.assertEqual(config["timeout"], 30)

    def _get_invoice_candidate(self):
        invoice_ids = self.invoice_obj.search(
            self.cursor,
            self.uid,
            [
                ("type", "=", "out_invoice"),
                ("state", "=", "open"),
                ("payment_order_id", "=", False),
                ("residual", ">", 0),
            ],
            limit=1,
        )
        if not invoice_ids:
            self.fail("Cal una factura de client per provar Redsys")

        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        polissa = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        invoice = self.invoice_obj.browse(self.cursor, self.uid, invoice_ids[0])
        factura_id = self.factura_obj.create(
            self.cursor,
            self.uid,
            {
                "invoice_id": invoice.id,
                "polissa_id": polissa.id,
                "tarifa_acces_id": polissa.tarifa.id,
                "cups_id": polissa.cups.id,
                "llista_preu": polissa.llista_preu.id,
                "potencia": 1,
                "date_boe": "2021-01-01",
                "facturacio": 1,
            },
        )
        return self.factura_obj.browse(self.cursor, self.uid, factura_id)

    def _prepare_eligible_invoice(self):
        factura = self._get_invoice_candidate()
        invoice = factura.invoice_id
        token = "tok_redsys_%s_%s" % (invoice.id, int(time.time() * 1000000))
        card_id = self.card_obj.create(
            self.cursor,
            self.uid,
            {
                "partner_id": factura.polissa_id.pagador.id,
                "token": token,
                "cof_txnid": "cof_txnid_%s" % invoice.id,
                "masked_number": "**** **** **** 4242",
                "expiry_date": "12/35",
                "active": True,
            },
        )
        self.factura_obj.write(
            self.cursor,
            self.uid,
            [factura.id],
            {
                "redsys_collection_state": False,
                "redsys_order_ref": False,
                "redsys_card_id": False,
                "redsys_amount_cents": False,
                "redsys_currency": False,
                "redsys_response_code": False,
                "redsys_response_message": False,
            },
        )
        self.invoice_obj.write(
            self.cursor,
            self.uid,
            [invoice.id],
            {
                "payment_type": self.card_type_id,
                "date_due": date.today().strftime("%Y-%m-%d"),
                "comment": False,
                "pending_state": False,
            },
        )
        self.polissa_obj.write(
            self.cursor, self.uid, [factura.polissa_id.id], {"creditcard": card_id}
        )
        return self.factura_obj.browse(self.cursor, self.uid, factura.id)

    def _redsys_client(self, response=None, exception=None):
        client = mock.Mock()
        if exception:
            client.mit_payment.side_effect = exception
        else:
            client.mit_payment.return_value = response
        return mock.patch("sermepa.RestClient", return_value=client), client

    def test_search_recurrent_card_factura_ids_uses_real_invoice_and_card(self):
        invoice = self._prepare_eligible_invoice()

        eligible_ids = self.factura_obj._search_recurrent_card_factura_ids(
            self.cursor, self.uid
        )

        self.assertIn(invoice.id, eligible_ids)

    def test_search_recurrent_card_factura_ids_skips_factura_not_due(self):
        invoice = self._prepare_eligible_invoice()
        tomorrow = date.today() + timedelta(days=1)
        self.factura_obj.write(
            self.cursor,
            self.uid,
            [invoice.id],
            {"date_due": tomorrow.strftime("%Y-%m-%d")},
        )

        eligible_ids = self.factura_obj._search_recurrent_card_factura_ids(
            self.cursor, self.uid
        )

        self.assertNotIn(invoice.id, eligible_ids)

    def test_search_recurrent_card_factura_ids_skips_factura_under_review(self):
        invoice = self._prepare_eligible_invoice()
        self.factura_obj.write(
            self.cursor,
            self.uid,
            [invoice.id],
            {"redsys_collection_state": "review"},
        )

        eligible_ids = self.factura_obj._search_recurrent_card_factura_ids(
            self.cursor, self.uid
        )

        self.assertNotIn(invoice.id, eligible_ids)

    def test_charge_factura_by_redsys_marks_submitted_as_review_without_retry(self):
        factura = self._prepare_eligible_invoice()
        self.factura_obj.write(
            self.cursor,
            self.uid,
            [factura.id],
            {
                "redsys_collection_state": "submitted",
                "redsys_order_ref": "123SUBMITTED",
            },
        )
        redsys_client, client = self._redsys_client()

        with redsys_client:
            result = self.factura_obj._charge_factura_by_redsys(
                self.cursor, self.uid, factura.id
            )

        self.assertTrue(result)
        client.mit_payment.assert_not_called()
        updated_factura = self.factura_obj.browse(self.cursor, self.uid, factura.id)
        self.assertEqual(updated_factura.redsys_collection_state, "review")
        self.assertIn(u"123SUBMITTED", updated_factura.redsys_response_message)
        self.assertIn(u"unknown", updated_factura.redsys_response_message)
        self.assertIn(u"Manual reconciliation", updated_factura.redsys_response_message)

    def test_build_redsys_transaction_params_uses_real_configuration_and_card(self):
        invoice = self._prepare_eligible_invoice()
        card = invoice and self.factura_obj._get_recurrent_card_for_factura(
            self.cursor, self.uid, invoice
        )

        params, order_ref = self.factura_obj._build_redsys_transaction_params(
            self.cursor, self.uid, invoice, card
        )

        self.assertEqual(len(order_ref), 12)
        self.assertEqual(params["Ds_Merchant_Order"], order_ref)
        self.assertEqual(params["Ds_Merchant_MerchantCode"], "999008881")
        self.assertEqual(params["Ds_Merchant_Identifier"], card.token)
        self.assertEqual(params["Ds_Merchant_Cof_TxnID"], card.cof_txnid)
        self.assertNotIn("Ds_Merchant_Cof_INI", params)
        self.assertEqual(params["Ds_Merchant_Cof_Type"], "R")
        self.assertEqual(params["Ds_Merchant_Excep_SCA"], "MIT")

    def test_charge_factura_by_redsys_advances_pending_on_confirmed_failure(self):
        invoice = self._prepare_eligible_invoice()
        response = {
            "raw": {"Ds_Response": "101", "error": "Operacio denegada"},
            "merchant_parameters": {"Ds_Response": "101"},
        }
        redsys_client, client = self._redsys_client(response=response)

        with redsys_client:
            with mock.patch.object(self.factura_obj, "go_on_pending") as go_on_pending:
                with mock.patch.object(self.factura_obj, "set_pending") as set_pending:
                    result = self.factura_obj._charge_factura_by_redsys(
                        self.cursor, self.uid, invoice.id
                    )

        self.assertTrue(result)
        client.mit_payment.assert_called_once()
        go_on_pending.assert_called_once_with(
            self.cursor, self.uid, [invoice.id], context={}
        )
        set_pending.assert_not_called()
        updated_factura = self.factura_obj.browse(self.cursor, self.uid, invoice.id)
        self.assertFalse(updated_factura.pending_state)
        self.assertEqual(updated_factura.redsys_collection_state, "declined")
        self.assertEqual(updated_factura.redsys_response_code, "101")
        self.assertIn(u"Operacio denegada", updated_factura.redsys_response_message)

    def test_charge_factura_by_redsys_keeps_factura_eligible_when_tpv_is_unconfigured(self):
        factura = self._prepare_eligible_invoice()
        self.config_obj.set(self.cursor, self.uid, "redsys_tpv_journal_id", "")
        self.config_obj.set(
            self.cursor, self.uid, "redsys_tpv_journal_code", "CARD"
        )
        redsys_client, client = self._redsys_client()

        with redsys_client:
            with self.assertRaises(osv.except_osv) as error:
                self.factura_obj._charge_factura_by_redsys(
                    self.cursor, self.uid, factura.id
                )

        self.assertIn("redsys_tpv_journal_id", error.exception.value)
        client.mit_payment.assert_not_called()
        updated_factura = self.factura_obj.browse(self.cursor, self.uid, factura.id)
        self.assertFalse(updated_factura.redsys_collection_state)
        eligible_ids = self.factura_obj._search_recurrent_card_factura_ids(
            self.cursor, self.uid
        )
        self.assertIn(factura.id, eligible_ids)

    def test_get_tpv_payment_data_uses_configured_account_over_journal_defaults(self):
        payment_mode_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_mode_card_recurrent"
        )[1]
        payment_mode = self.openerp.pool.get("payment.mode").browse(
            self.cursor, self.uid, payment_mode_id
        )
        account_ids = self.account_obj.search(
            self.cursor,
            self.uid,
            [("id", "!=", payment_mode.journal.default_credit_account_id.id)],
            limit=1,
        )
        self.assertTrue(account_ids)
        self.config_obj.set(
            self.cursor,
            self.uid,
            "redsys_tpv_pay_account_id",
            str(account_ids[0]),
        )

        payment_data = self.factura_obj._get_tpv_payment_data(
            self.cursor, self.uid
        )

        self.assertEqual(payment_data["journal_id"], payment_mode.journal.id)
        self.assertEqual(payment_data["pay_account_id"], account_ids[0])

    def test_get_tpv_payment_data_requires_configured_payment_account(self):
        self.config_obj.set(self.cursor, self.uid, "redsys_tpv_pay_account_id", "")

        with self.assertRaises(osv.except_osv) as error:
            self.factura_obj._get_tpv_payment_data(self.cursor, self.uid)

        self.assertIn("redsys_tpv_pay_account_id", error.exception.value)

    def test_charge_factura_by_redsys_marks_approved_payment_as_paid(self):
        invoice = self._prepare_eligible_invoice()
        initial_residual = invoice.invoice_id.residual
        response = {
            "raw": {"Ds_Response": "0000"},
            "merchant_parameters": {"Ds_Response": "0000"},
        }
        redsys_client, client = self._redsys_client(response=response)

        with redsys_client:
            result = self.factura_obj._charge_factura_by_redsys(
                self.cursor, self.uid, invoice.id
            )

        self.assertTrue(result)
        client.mit_payment.assert_called_once()
        updated_factura = self.factura_obj.browse(self.cursor, self.uid, invoice.id)
        self.assertEqual(updated_factura.redsys_collection_state, "paid")
        self.assertEqual(updated_factura.redsys_response_code, "0000")
        self.assertLess(updated_factura.invoice_id.residual, initial_residual)

    def test_charge_factura_by_redsys_marks_transport_failure_for_review(self):
        invoice = self._prepare_eligible_invoice()
        redsys_client, client = self._redsys_client(exception=Exception("timeout"))

        with redsys_client:
            result = self.factura_obj._charge_factura_by_redsys(
                self.cursor, self.uid, invoice.id
            )

        self.assertTrue(result)
        client.mit_payment.assert_called_once()
        updated_factura = self.factura_obj.browse(self.cursor, self.uid, invoice.id)
        self.assertFalse(updated_factura.pending_state)
        self.assertEqual(updated_factura.redsys_collection_state, "review")
        self.assertIn(u"timeout", updated_factura.redsys_response_message)

    def test_charge_factura_by_redsys_marks_malformed_response_for_review(self):
        invoice = self._prepare_eligible_invoice()
        redsys_client, client = self._redsys_client(response="invalid response")

        with redsys_client:
            result = self.factura_obj._charge_factura_by_redsys(
                self.cursor, self.uid, invoice.id
            )

        self.assertTrue(result)
        client.mit_payment.assert_called_once()
        updated_factura = self.factura_obj.browse(self.cursor, self.uid, invoice.id)
        self.assertEqual(updated_factura.redsys_collection_state, "review")
        self.assertIn(
            u"object has no attribute", updated_factura.redsys_response_message
        )

    def test_build_redsys_order_returns_unique_twelve_character_references(self):
        first_order = self.factura_obj._build_redsys_order(1234)
        second_order = self.factura_obj._build_redsys_order(11234)

        self.assertEqual(len(first_order), 12)
        self.assertEqual(len(second_order), 12)
        self.assertNotEqual(first_order, second_order)
