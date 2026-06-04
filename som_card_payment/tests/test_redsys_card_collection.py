# -*- coding: utf-8 -*-

from datetime import date
import time

from destral import testing
import mock

from som_card_payment.models import account_invoice as card_account_invoice


class FakeRedsysClient(object):
    def __init__(self, response):
        self.response = response
        self.calls = []

    def mit_payment(self, params):
        self.calls.append(params)
        return self.response


class FakeRedsysExceptionClient(object):
    def __init__(self, exception):
        self.exception = exception
        self.calls = []

    def mit_payment(self, params):
        self.calls.append(params)
        raise self.exception


class FakeRecord(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeCursor(object):
    def __init__(self, execute_error=None):
        self.execute_error = execute_error
        self.executed = []
        self.savepoints = []
        self.rollbacks = []
        self.commits = 0

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if self.execute_error:
            raise self.execute_error

    def savepoint(self, name):
        self.savepoints.append(name)

    def rollback(self, name=None):
        self.rollbacks.append(name)

    def commit(self):
        self.commits += 1


class FakeLockException(Exception):
    pgcode = "55P03"


class TestRedsysCardCollection(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRedsysCardCollection, self).setUp()
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.invoice_obj = self.openerp.pool.get("account.invoice")
        self.factura_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        self.card_obj = self.openerp.pool.get("res.partner.creditcard")
        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")

        self.card_type_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        self.pending_state_id = self.imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "account_invoice_pending",
            "default_invoice_pending_state",
        )[1]

    def _get_invoice_candidate(self):
        factura_ids = self.factura_obj.search(
            self.cursor,
            self.uid,
            [
                ("type", "=", "out_invoice"),
                ("state", "=", "open"),
                ("payment_order_id", "=", False),
                ("polissa_id", "!=", False),
            ],
            limit=20,
        )
        if not factura_ids:
            self.skipTest("No hi ha factures obertes disponibles per provar Redsys")
        factura = self.factura_obj.browse(self.cursor, self.uid, factura_ids[0])
        return factura.invoice_id.id

    def _recurrent_payment_type(self):
        return FakeRecord(code="COBRAMENT_RECURRENT_TARGETA")

    def _prepare_eligible_invoice(self):
        invoice_id = self._get_invoice_candidate()
        invoice = self.invoice_obj.browse(self.cursor, self.uid, invoice_id)
        factura = self.invoice_obj._get_factura_for_invoice(
            self.cursor, self.uid, invoice
        )
        if not factura or not factura.polissa_id:
            self.skipTest("No hi ha factura amb polissa disponible per provar Redsys")

        existing_card_ids = self.card_obj.search(
            self.cursor, self.uid, [("partner_id", "=", factura.polissa_id.pagador.id)]
        )
        if existing_card_ids:
            self.card_obj.write(
                self.cursor,
                self.uid,
                existing_card_ids,
                {"active": False},
            )

        card_id = self.card_obj.create(
            self.cursor,
            self.uid,
            {
                "partner_id": factura.polissa_id.pagador.id,
                "token": "tok_redsys_%s_%s" % (invoice_id, int(time.time() * 1000000)),
                "cof_txnid": "cof_txnid_%s" % invoice_id,
                "masked_number": "**** **** **** 4242",
                "expiry_date": "12/35",
                "active": True,
            },
        )

        self.invoice_obj.write(
            self.cursor,
            self.uid,
            [invoice_id],
            {
                "payment_type": self.card_type_id,
                "date_due": date.today().strftime("%Y-%m-%d"),
            },
        )
        self.polissa_obj.write(
            self.cursor,
            self.uid,
            [factura.polissa_id.id],
            {"creditcard": card_id},
        )
        return invoice_id, card_id

    def test_search_recurrent_card_invoice_ids_checks_due_date_and_card(self):
        invoice = FakeRecord(id=1)
        invoice_without_card = FakeRecord(id=2)
        invoice_pending_review = FakeRecord(
            id=3,
            comment=u"Redsys targeta recurrent pendent revisio - ordre 12340000ABCD",
        )
        invoice_failed_ko = FakeRecord(
            id=4,
            comment=(
                u"2026-06-04 - Redsys targeta recurrent KO - factura F2026/0001 "
                u"- ordre 12340000ABCD - codi 101 - Operación denegada"
            ),
        )
        factura = FakeRecord(invoice_id=invoice)
        factura_duplicate = FakeRecord(invoice_id=invoice)
        factura_without_card = FakeRecord(invoice_id=invoice_without_card)
        factura_pending_review = FakeRecord(invoice_id=invoice_pending_review)
        factura_failed_ko = FakeRecord(invoice_id=invoice_failed_ko)

        with mock.patch.object(
            self.invoice_obj,
            "search",
            return_value=[
                invoice.id,
                invoice.id,
                invoice_without_card.id,
                invoice_pending_review.id,
                invoice_failed_ko.id,
            ],
        ) as mock_invoice_search, mock.patch.object(
            self.factura_obj,
            "search",
            return_value=[10, 11, 12, 13, 14],
        ) as mock_factura_search, mock.patch.object(
            self.factura_obj,
            "browse",
            return_value=[
                factura,
                factura_duplicate,
                factura_without_card,
                factura_pending_review,
                factura_failed_ko,
            ],
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_recurrent_card_for_invoice",
            side_effect=[FakeRecord(id=55), False],
        ) as mock_get_card:
            eligible_ids = self.invoice_obj._search_recurrent_card_invoice_ids(
                self.cursor, self.uid
            )

        self.assertEqual(eligible_ids, [invoice.id])
        self.assertEqual(mock_get_card.call_count, 2)
        invoice_domain = mock_invoice_search.call_args[0][2]
        self.assertIn(("date_due", "<=", date.today().strftime("%Y-%m-%d")), invoice_domain)
        mock_factura_search.assert_called_once()

    def test_search_recurrent_card_invoice_ids_requires_contract_selected_card(self):
        invoice = FakeRecord(id=1234)
        pagador = FakeRecord(id=77)
        card = FakeRecord(
            active=True, token="TOKEN123", cof_txnid="COF123", partner_id=pagador
        )
        polissa = FakeRecord(creditcard=False, pagador=pagador)
        factura = FakeRecord(polissa_id=polissa)

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_factura_for_invoice",
            return_value=factura,
        ):
            self.assertFalse(
                self.invoice_obj._get_recurrent_card_for_invoice(
                    self.cursor, self.uid, invoice
                )
            )

            polissa.creditcard = card
            card.cof_txnid = False
            self.assertFalse(
                self.invoice_obj._get_recurrent_card_for_invoice(
                    self.cursor, self.uid, invoice
                )
            )

            card.cof_txnid = "COF123"
            self.assertEqual(
                self.invoice_obj._get_recurrent_card_for_invoice(
                    self.cursor, self.uid, invoice
                ),
                card,
            )

            card.partner_id = FakeRecord(id=88)
            self.assertFalse(
                self.invoice_obj._get_recurrent_card_for_invoice(
                    self.cursor, self.uid, invoice
                )
            )

    def test_is_recurrent_card_invoice_still_collectable_requires_recurrent_payment_type(self):
        recurrent_type = FakeRecord(code="COBRAMENT_RECURRENT_TARGETA")
        other_type = FakeRecord(code="RECIBO_CSB")
        collectable = FakeRecord(
            state="open",
            type="out_invoice",
            payment_order_id=False,
            residual=12.34,
            date_due=date.today().strftime("%Y-%m-%d"),
            payment_type=recurrent_type,
        )

        self.assertTrue(
            self.invoice_obj._is_recurrent_card_invoice_still_collectable(collectable)
        )

        collectable.payment_type = False
        self.assertFalse(
            self.invoice_obj._is_recurrent_card_invoice_still_collectable(collectable)
        )

        collectable.payment_type = other_type
        self.assertFalse(
            self.invoice_obj._is_recurrent_card_invoice_still_collectable(collectable)
        )

    def test_build_redsys_transaction_params_includes_mit_fields(self):
        invoice = FakeRecord(id=1234, residual=12.34, number="F2026/0001", name=False)
        card = FakeRecord(token="TOKEN123", cof_txnid="COF123")

        expected_order = "12340000ABCD"
        expected_config = {
            "merchant_code": "999008881",
            "private_key": "secret",
            "merchant_url": "https://merchant.local/notify",
            "endpoint_url": "https://sis.redsys.es/sis/rest/trataPeticionREST",
            "terminal": "1",
            "currency": "978",
            "timeout": 30,
        }

        with mock.patch.object(
            card_account_invoice.AccountInvoice, "_get_redsys_config"
        ) as mock_config, mock.patch.object(
            card_account_invoice.AccountInvoice, "_build_redsys_order",
            return_value=expected_order,
        ):
            mock_config.return_value = expected_config
            params, order_ref = self.invoice_obj._build_redsys_transaction_params(
                self.cursor, self.uid, invoice, card
            )

        self.assertEqual(order_ref, expected_order)
        self.assertEqual(params["Ds_Merchant_Amount"], "1234")
        self.assertEqual(params["Ds_Merchant_Order"], expected_order)
        self.assertEqual(
            params["Ds_Merchant_MerchantCode"], expected_config["merchant_code"]
        )
        self.assertEqual(params["Ds_Merchant_Currency"], expected_config["currency"])
        self.assertEqual(params["Ds_Merchant_TransactionType"], "0")
        self.assertEqual(params["Ds_Merchant_Terminal"], expected_config["terminal"])
        self.assertEqual(
            params["Ds_Merchant_MerchantURL"], expected_config["merchant_url"]
        )
        self.assertEqual(params["Ds_Merchant_SumTotal"], params["Ds_Merchant_Amount"])
        self.assertEqual(params["Ds_Merchant_Identifier"], card.token)
        self.assertEqual(params["Ds_Merchant_Cof_TxnID"], card.cof_txnid)
        self.assertEqual(params["Ds_Merchant_Cof_INI"], "N")
        self.assertEqual(params["Ds_Merchant_Cof_Type"], "C")
        self.assertEqual(params["Ds_Merchant_Excep_SCA"], "MIT")
        self.assertEqual(params["Ds_Merchant_DirectPayment"], "true")
        self.assertEqual(params["Ds_Merchant_PayMethods"], "C")

    def test_build_redsys_transaction_params_rounds_half_cents_up(self):
        invoice = FakeRecord(id=1234, residual=10.005, number="F2026/0001", name=False)
        card = FakeRecord(token="TOKEN123", cof_txnid="COF123")

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_config",
            return_value={
                "merchant_code": "999008881",
                "private_key": "secret",
                "merchant_url": "https://merchant.local/notify",
                "endpoint_url": "https://sis.redsys.es/sis/rest/trataPeticionREST",
                "terminal": "1",
                "currency": "978",
                "timeout": 30,
            },
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_build_redsys_order",
            return_value="12340000ABCD",
        ):
            params, _order_ref = self.invoice_obj._build_redsys_transaction_params(
                self.cursor, self.uid, invoice, card
            )

        self.assertEqual(params["Ds_Merchant_Amount"], "1001")

    def test_build_redsys_order_uses_unique_twelve_char_reference(self):
        with mock.patch.object(card_account_invoice.time, "time", return_value=12345.678901):
            first_order = self.invoice_obj._build_redsys_order(1234)
            second_order = self.invoice_obj._build_redsys_order(11234)

        self.assertEqual(len(first_order), 12)
        self.assertEqual(len(second_order), 12)
        self.assertNotEqual(first_order, second_order)

    def test_cron_collect_recurrent_card_invoices_calls_charge_for_each_invoice(self):
        invoice_id = 1234
        fake_cursor = FakeCursor()

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_search_recurrent_card_invoice_ids",
            return_value=[invoice_id, invoice_id + 1],
        ) as mock_search, mock.patch.object(
            card_account_invoice.AccountInvoice, "_charge_invoice_by_redsys"
        ) as mock_charge:
            self.invoice_obj._cron_collect_recurrent_card_invoices(fake_cursor, self.uid)

        mock_search.assert_called_once()
        self.assertEqual(mock_charge.call_count, 2)
        self.assertEqual(mock_charge.call_args_list[0][0][2], invoice_id)

    def test_cron_collect_recurrent_card_invoices_commits_processed_invoices(self):
        fake_cursor = FakeCursor()

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_search_recurrent_card_invoice_ids",
            return_value=[11, 22, 33],
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_charge_invoice_by_redsys",
            side_effect=[True, Exception("unexpected failure"), False],
        ) as mock_charge:
            result = self.invoice_obj._cron_collect_recurrent_card_invoices(
                fake_cursor, self.uid
            )

        self.assertTrue(result)
        self.assertEqual(mock_charge.call_count, 3)
        self.assertEqual(fake_cursor.commits, 1)
        self.assertEqual(len(fake_cursor.rollbacks), 2)

    def test_cron_collect_recurrent_card_invoices_logs_unexpected_exception(self):
        fake_cursor = FakeCursor()

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_search_recurrent_card_invoice_ids",
            return_value=[11, 22],
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_charge_invoice_by_redsys",
            side_effect=[Exception("unexpected failure"), True],
        ), mock.patch.object(
            card_account_invoice.logger,
            "exception",
        ) as mock_exception:
            result = self.invoice_obj._cron_collect_recurrent_card_invoices(
                fake_cursor, self.uid
            )

        self.assertTrue(result)
        mock_exception.assert_called_once()
        self.assertIn("Unexpected Redsys", mock_exception.call_args[0][0])
        self.assertEqual(mock_exception.call_args[0][1], 11)
        self.assertEqual(fake_cursor.commits, 1)

    def test_cron_collect_recurrent_card_invoices_rolls_back_noop_invoice(self):
        fake_cursor = FakeCursor()

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_search_recurrent_card_invoice_ids",
            return_value=[11],
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_charge_invoice_by_redsys",
            return_value=False,
        ):
            result = self.invoice_obj._cron_collect_recurrent_card_invoices(
                fake_cursor, self.uid
            )

        self.assertTrue(result)
        self.assertEqual(fake_cursor.commits, 0)
        self.assertEqual(len(fake_cursor.rollbacks), 1)

    def test_charge_invoice_by_redsys_skips_when_invoice_lock_is_owned(self):
        invoice_id = 1234

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_lock_redsys_invoice_for_collection",
            return_value=False,
        ), mock.patch.object(
            self.invoice_obj,
            "browse",
        ) as mock_browse, mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_client",
        ) as mock_client:
            result = self.invoice_obj._charge_invoice_by_redsys(
                self.cursor, self.uid, invoice_id
            )

        self.assertFalse(result)
        mock_browse.assert_not_called()
        mock_client.assert_not_called()

    def test_lock_redsys_invoice_for_collection_skips_nowait_conflict(self):
        fake_cursor = FakeCursor(execute_error=FakeLockException())

        locked = self.invoice_obj._lock_redsys_invoice_for_collection(
            fake_cursor, self.uid, 1234
        )

        self.assertFalse(locked)
        self.assertEqual(len(fake_cursor.savepoints), 1)
        self.assertEqual(fake_cursor.rollbacks, fake_cursor.savepoints)

    def test_charge_invoice_by_redsys_revalidates_markers_after_lock(self):
        invoice_id = 1234
        invoice = FakeRecord(
            id=invoice_id,
            residual=12.34,
            number="F2026/0001",
            comment=u"Redsys targeta recurrent pendent revisio - ordre 12340000ABCD",
            payment_type=self._recurrent_payment_type(),
        )

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_lock_redsys_invoice_for_collection",
            return_value=True,
        ), mock.patch.object(
            self.invoice_obj,
            "browse",
            return_value=invoice,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_recurrent_card_for_invoice",
        ) as mock_card, mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_client",
        ) as mock_client:
            result = self.invoice_obj._charge_invoice_by_redsys(
                self.cursor, self.uid, invoice_id
            )

        self.assertFalse(result)
        mock_card.assert_not_called()
        mock_client.assert_not_called()

    def test_pay_invoice_by_tpv_uses_existing_payment_flow(self):
        invoice_id = 1234
        invoice = FakeRecord(
            id=invoice_id,
            residual=12.34,
            number="F2026/0001",
            name=False,
        )

        payment_data = {
            "journal_id": 11,
            "pay_account_id": 22,
            "period_id": 33,
        }

        with mock.patch.object(
            card_account_invoice.AccountInvoice, "_get_tpv_payment_data",
            return_value=payment_data,
        ), mock.patch.object(
            self.invoice_obj, "pay_and_reconcile"
        ) as mock_pay:
            self.invoice_obj._pay_invoice_by_tpv(self.cursor, self.uid, invoice)

        mock_pay.assert_called_once()
        args, kwargs = mock_pay.call_args
        self.assertEqual(args[0], self.cursor)
        self.assertEqual(args[1], self.uid)
        self.assertEqual(args[2], [invoice_id])
        self.assertEqual(args[3], invoice.residual)
        self.assertEqual(args[4], payment_data["pay_account_id"])
        self.assertEqual(args[5], payment_data["period_id"])
        self.assertEqual(args[6], payment_data["journal_id"])
        self.assertFalse(args[7])
        self.assertEqual(args[8], payment_data["period_id"])
        self.assertFalse(args[9])
        self.assertEqual(
            kwargs["name"], invoice.number or invoice.name or str(invoice.id)
        )
        self.assertEqual(kwargs["context"]["date_p"], date.today().strftime("%Y-%m-%d"))

    def test_charge_invoice_by_redsys_success_routes_to_tpv_payment(self):
        invoice_id = 1234
        invoice = FakeRecord(
            id=invoice_id,
            residual=12.34,
            number="F2026/0001",
            payment_type=self._recurrent_payment_type(),
        )
        card = FakeRecord(token="TOKEN123", cof_txnid="COF123")

        params = {
            "Ds_Merchant_Amount": "123",
            "Ds_Merchant_Order": "12340000ABCD",
            "Ds_Merchant_MerchantCode": "999008881",
            "Ds_Merchant_Currency": "978",
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Terminal": "1",
            "Ds_Merchant_MerchantURL": "https://merchant.local/notify",
            "Ds_Merchant_SumTotal": "123",
            "Ds_Merchant_Identifier": "TOKEN123",
            "Ds_Merchant_Cof_INI": "N",
            "Ds_Merchant_Cof_Type": "C",
            "Ds_Merchant_Excep_SCA": "MIT",
            "Ds_Merchant_DirectPayment": "true",
            "Ds_Merchant_PayMethods": "C",
            "Ds_Merchant_MerchantData": "invoice:123",
        }
        client = FakeRedsysClient(
            {
                "raw": {"Ds_Response": "0000"},
                "merchant_parameters": {"Ds_Response": "0000"},
            }
        )
        payment_data = {
            "journal_id": 11,
            "pay_account_id": 22,
            "period_id": 33,
        }

        with mock.patch.object(
            self.invoice_obj,
            "browse",
            return_value=invoice,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_recurrent_card_for_invoice",
            return_value=card,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_tpv_payment_data",
            return_value=payment_data,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_build_redsys_transaction_params",
            return_value=(params, params["Ds_Merchant_Order"]),
        ) as mock_build, mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_client",
            return_value=client,
        ) as mock_client, mock.patch.object(
            card_account_invoice.AccountInvoice, "_pay_invoice_by_tpv"
        ) as mock_pay, mock.patch.object(
            card_account_invoice.AccountInvoice, "_register_redsys_failure"
        ) as mock_fail:
            self.invoice_obj._charge_invoice_by_redsys(self.cursor, self.uid, invoice_id)

        mock_build.assert_called_once()
        mock_client.assert_called_once()
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0], params)
        mock_pay.assert_called_once()
        self.assertEqual(mock_pay.call_args[0][2].id, invoice_id)
        self.assertEqual(mock_pay.call_args[1]["payment_data"], payment_data)
        mock_fail.assert_not_called()

    def test_charge_invoice_success_reconcile_failure_is_not_retried_as_redsys_ko(self):
        invoice_id = 1234
        invoice = FakeRecord(
            id=invoice_id,
            residual=12.34,
            number="F2026/0001",
            name=False,
            comment=u"Comentari existent",
            payment_type=self._recurrent_payment_type(),
        )
        card = FakeRecord(token="TOKEN123", cof_txnid="COF123")
        params = {
            "Ds_Merchant_Amount": "123",
            "Ds_Merchant_Order": "12340000ABCD",
            "Ds_Merchant_MerchantCode": "999008881",
            "Ds_Merchant_Currency": "978",
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Terminal": "1",
            "Ds_Merchant_MerchantURL": "https://merchant.local/notify",
            "Ds_Merchant_SumTotal": "123",
            "Ds_Merchant_Identifier": "TOKEN123",
            "Ds_Merchant_Cof_INI": "N",
            "Ds_Merchant_Cof_Type": "C",
            "Ds_Merchant_Excep_SCA": "MIT",
            "Ds_Merchant_DirectPayment": "true",
            "Ds_Merchant_PayMethods": "C",
            "Ds_Merchant_MerchantData": "invoice:123",
        }
        client = FakeRedsysClient(
            {
                "raw": {"Ds_Response": "0000"},
                "merchant_parameters": {"Ds_Response": "0000"},
            }
        )
        payment_data = {
            "journal_id": 11,
            "pay_account_id": 22,
            "period_id": 33,
        }

        with mock.patch.object(
            self.invoice_obj,
            "browse",
            return_value=invoice,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_recurrent_card_for_invoice",
            return_value=card,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_tpv_payment_data",
            return_value=payment_data,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_build_redsys_transaction_params",
            return_value=(params, params["Ds_Merchant_Order"]),
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_client",
            return_value=client,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_pay_invoice_by_tpv",
            side_effect=Exception("Conciliacion fallida"),
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_register_redsys_failure",
        ) as mock_fail, mock.patch.object(
            self.invoice_obj,
            "write",
        ) as mock_write:
            result = self.invoice_obj._charge_invoice_by_redsys(
                self.cursor, self.uid, invoice_id
            )

        self.assertTrue(result)
        self.assertEqual(len(client.calls), 1)
        mock_fail.assert_not_called()
        mock_write.assert_called_once()
        written_comment = mock_write.call_args[0][3]["comment"]
        self.assertIn(u"Redsys targeta recurrent OK pendent conciliacio", written_comment)
        self.assertIn(invoice.comment, written_comment)

    def test_charge_invoice_success_reconcile_failure_rolls_back_before_marker(self):
        invoice_id = 1234
        invoice = FakeRecord(
            id=invoice_id,
            residual=12.34,
            number="F2026/0001",
            name=False,
            comment=u"Comentari existent",
            payment_type=self._recurrent_payment_type(),
        )
        card = FakeRecord(token="TOKEN123", cof_txnid="COF123")
        fixed_order = "12340000ABCD"
        params = {
            "Ds_Merchant_Amount": "123",
            "Ds_Merchant_Order": fixed_order,
            "Ds_Merchant_MerchantCode": "999008881",
            "Ds_Merchant_Currency": "978",
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Terminal": "1",
            "Ds_Merchant_MerchantURL": "https://merchant.local/notify",
            "Ds_Merchant_SumTotal": "123",
            "Ds_Merchant_Identifier": "TOKEN123",
            "Ds_Merchant_Cof_INI": "N",
            "Ds_Merchant_Cof_Type": "C",
            "Ds_Merchant_Excep_SCA": "MIT",
            "Ds_Merchant_DirectPayment": "true",
            "Ds_Merchant_PayMethods": "C",
            "Ds_Merchant_MerchantData": "invoice:123",
        }
        client = FakeRedsysClient(
            {
                "raw": {"Ds_Response": "0000"},
                "merchant_parameters": {"Ds_Response": "0000"},
            }
        )
        fake_cursor = FakeCursor()
        payment_data = {
            "journal_id": 11,
            "pay_account_id": 22,
            "period_id": 33,
        }

        def assert_transaction_was_rolled_back(cursor, uid, ids, vals, context=None):
            rolled_back = [
                name for name in fake_cursor.rollbacks
                if name.startswith("redsys_card_success_reconcile_%s_" % invoice_id)
            ]
            self.assertTrue(rolled_back)
            self.assertIn(
                u"Redsys targeta recurrent OK pendent conciliacio",
                vals["comment"],
            )

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_lock_redsys_invoice_for_collection",
            return_value=True,
        ), mock.patch.object(
            self.invoice_obj,
            "browse",
            return_value=invoice,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_recurrent_card_for_invoice",
            return_value=card,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_tpv_payment_data",
            return_value=payment_data,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_build_redsys_transaction_params",
            return_value=(params, fixed_order),
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_client",
            return_value=client,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_pay_invoice_by_tpv",
            side_effect=Exception("DB transaction aborted"),
        ), mock.patch.object(
            self.invoice_obj,
            "write",
            side_effect=assert_transaction_was_rolled_back,
        ) as mock_write:
            result = self.invoice_obj._charge_invoice_by_redsys(
                fake_cursor, self.uid, invoice_id
            )

        self.assertTrue(result)
        mock_write.assert_called_once()

    def test_charge_invoice_transport_exception_marks_manual_review_not_ko(self):
        invoice_id = 1234
        invoice = FakeRecord(
            id=invoice_id,
            residual=12.34,
            number="F2026/0001",
            name=False,
            comment=u"Comentari existent",
            payment_type=self._recurrent_payment_type(),
        )
        card = FakeRecord(token="TOKEN123", cof_txnid="COF123")
        fixed_order = "12340000ABCD"
        params = {
            "Ds_Merchant_Amount": "123",
            "Ds_Merchant_Order": fixed_order,
            "Ds_Merchant_MerchantCode": "999008881",
            "Ds_Merchant_Currency": "978",
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Terminal": "1",
            "Ds_Merchant_MerchantURL": "https://merchant.local/notify",
            "Ds_Merchant_SumTotal": "123",
            "Ds_Merchant_Identifier": "TOKEN123",
            "Ds_Merchant_Cof_INI": "N",
            "Ds_Merchant_Cof_Type": "C",
            "Ds_Merchant_Excep_SCA": "MIT",
            "Ds_Merchant_DirectPayment": "true",
            "Ds_Merchant_PayMethods": "C",
            "Ds_Merchant_MerchantData": "invoice:123",
        }
        client = FakeRedsysExceptionClient(Exception("timeout after submit"))
        payment_data = {
            "journal_id": 11,
            "pay_account_id": 22,
            "period_id": 33,
        }

        with mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_lock_redsys_invoice_for_collection",
            return_value=True,
        ), mock.patch.object(
            self.invoice_obj,
            "browse",
            return_value=invoice,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_recurrent_card_for_invoice",
            return_value=card,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_tpv_payment_data",
            return_value=payment_data,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_build_redsys_transaction_params",
            return_value=(params, fixed_order),
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_client",
            return_value=client,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_register_redsys_failure",
        ) as mock_failure, mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_set_redsys_failure_pending",
        ) as mock_pending, mock.patch.object(
            self.invoice_obj,
            "write",
        ) as mock_write:
            result = self.invoice_obj._charge_invoice_by_redsys(
                self.cursor, self.uid, invoice_id
            )

        self.assertTrue(result)
        self.assertEqual(len(client.calls), 1)
        mock_failure.assert_not_called()
        mock_pending.assert_not_called()
        mock_write.assert_called_once()
        written_comment = mock_write.call_args[0][3]["comment"]
        self.assertIn(u"Redsys targeta recurrent pendent revisio", written_comment)
        self.assertIn(fixed_order, written_comment)
        self.assertIn(u"HTTP", written_comment)
        self.assertIn(u"timeout after submit", written_comment)
        self.assertIn(invoice.comment, written_comment)

    def test_charge_invoice_by_redsys_failure_records_note_and_pending_once(self):
        invoice_id = 1234
        invoice = FakeRecord(
            id=invoice_id,
            residual=12.34,
            number="F2026/0001",
            name=False,
            payment_type=self._recurrent_payment_type(),
        )
        card = FakeRecord(token="TOKEN123", cof_txnid="COF123")
        previous_comment = u"Comentari existent"
        invoice.comment = previous_comment
        invoice.pending_state = False

        fixed_order = "12340000ABCD"
        params = {
            "Ds_Merchant_Amount": "123",
            "Ds_Merchant_Order": fixed_order,
            "Ds_Merchant_MerchantCode": "999008881",
            "Ds_Merchant_Currency": "978",
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Terminal": "1",
            "Ds_Merchant_MerchantURL": "https://merchant.local/notify",
            "Ds_Merchant_SumTotal": "123",
            "Ds_Merchant_Identifier": "TOKEN123",
            "Ds_Merchant_Cof_INI": "N",
            "Ds_Merchant_Cof_Type": "C",
            "Ds_Merchant_Excep_SCA": "MIT",
            "Ds_Merchant_DirectPayment": "true",
            "Ds_Merchant_PayMethods": "C",
            "Ds_Merchant_MerchantData": "invoice:123",
        }
        client = FakeRedsysClient(
            {
                "raw": {"Ds_Response": "101", "error": "Operación denegada"},
                "merchant_parameters": {"Ds_Response": "101"},
            }
        )
        payment_data = {
            "journal_id": 11,
            "pay_account_id": 22,
            "period_id": 33,
        }

        with mock.patch.object(
            self.invoice_obj,
            "browse",
            return_value=invoice,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_recurrent_card_for_invoice",
            return_value=card,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_tpv_payment_data",
            return_value=payment_data,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_build_redsys_transaction_params",
            return_value=(params, fixed_order),
        ), mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_get_redsys_client",
            return_value=client,
        ), mock.patch.object(
            card_account_invoice.AccountInvoice, "_pay_invoice_by_tpv"
        ) as mock_pay, mock.patch.object(
            self.invoice_obj,
            "write",
        ) as mock_write, mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_set_redsys_failure_pending",
        ) as mock_pending:
            self.invoice_obj._charge_invoice_by_redsys(self.cursor, self.uid, invoice_id)

        mock_pay.assert_not_called()
        self.assertEqual(len(client.calls), 1)

        marker = u"ordre {} - codi 101".format(fixed_order)
        expected_note = (
            u"{} - Redsys targeta recurrent KO - factura {} - ordre {} "
            u"- codi 101 - Operación denegada"
        ).format(
            date.today().strftime("%Y-%m-%d"),
            invoice.number or invoice.name or str(invoice.id),
            fixed_order,
        )

        mock_write.assert_called_once()
        written_comment = mock_write.call_args[0][3]["comment"]
        self.assertEqual(written_comment.count(marker), 1)
        self.assertTrue(written_comment.startswith(expected_note))
        self.assertIn(previous_comment, written_comment)
        mock_pending.assert_called_once_with(
            self.cursor,
            self.uid,
            invoice_id,
            self.pending_state_id,
            context={},
        )

        invoice.comment = written_comment
        invoice.pending_state = FakeRecord(id=self.pending_state_id)
        with mock.patch.object(self.invoice_obj, "write") as duplicate_write, mock.patch.object(
            card_account_invoice.AccountInvoice,
            "_set_redsys_failure_pending",
        ) as duplicate_pending:
            registered = self.invoice_obj._register_redsys_failure(
                self.cursor,
                self.uid,
                invoice,
                fixed_order,
                "101",
                "Operación denegada",
            )

        self.assertFalse(registered)
        duplicate_write.assert_not_called()
        duplicate_pending.assert_not_called()
