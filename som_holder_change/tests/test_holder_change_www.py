# -*- coding: utf-8 -*-
from __future__ import absolute_import

from copy import deepcopy

import mock
import pooler
from destral import testing
from destral.patch import PatchNewCursors
from destral.transaction import Transaction
from som_holder_change.models import holder_change_reports
from tools import config


class TestHolderChangeWww(testing.OOTestCase):

    _local_service = (
        "som_holder_change.models.holder_change_request.netsvc.LocalService"
    )
    _subscribe_member = (
        "som_polissa_soci.models.res_partner_address."
        "ResPartnerAddress.subscribe_partner_in_members_lists"
    )
    _unsubscribe_customer = (
        "som_polissa_soci.models.res_partner_address."
        "ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists"
    )
    _subscribe_customer = (
        "som_polissa_soci.models.res_partner_address."
        "ResPartnerAddress.subscribe_partner_in_customers_no_members_lists"
    )

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.raw_cursor = self.cursor
        self.new_cursors = PatchNewCursors()
        self.new_cursors.__enter__()
        # The workflow commits and opens cursors to isolate simulations.
        # Use Destral's transaction cursor so teardown can roll them all back.
        self.cursor = pooler.get_db(self.cursor.dbname).cursor()
        self.uid = self.txn.user
        self.www_obj = self.openerp.pool.get("som.holder.change.www")
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        self._original_simulate_holder_change = self.request_obj._simulate_holder_change
        self._simulation_savepoint = 0
        self.simulate_holder_change = mock.patch.object(
            self.request_obj,
            "_simulate_holder_change",
            side_effect=self._simulate_holder_change,
        ).start()
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.polissa = self.polissa_obj.browse(
            self.cursor, self.uid, self.polissa_id
        )
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id, {"state": "activa"}
        )
        lang_obj = self.openerp.pool.get("res.lang")
        if not lang_obj.search(self.cursor, self.uid, [("code", "=", "ca_ES")]):
            lang_obj.create(self.cursor, self.uid, {"name": "Català", "code": "ca_ES"})
        # create_request commits so requests from prior tests survive in this DB.
        self.cursor.execute(
            "UPDATE som_holder_change_request SET state = 'completed' "
            "WHERE polissa_id = %s AND state IN %s",
            (self.polissa_id, (
                "received", "awaiting_payment", "awaiting_signature", "queued",
            )),
        )
        self.local_service_patch = mock.patch(self._local_service)
        self.local_service = self.local_service_patch.start()
        self.local_service.return_value.create.side_effect = self._create_report
        self.local_service.return_value._service.get_report_v.return_value = {
            "id": 1, "context": {},
        }
        self.local_service.return_value._service.create_html.side_effect = self._create_html_report
        self.render_card_reports = mock.patch.object(
            holder_change_reports, "render_snapshot",
            return_value={"contract_pdf": b"JVBERi1jYXJk", "mandate_pdf": False},
        ).start()
        self.send_mail = mock.patch.object(self.request_obj, "_send_mail").start()
        self.subscribe_member = mock.patch(self._subscribe_member).start()
        self.unsubscribe_customer = mock.patch(self._unsubscribe_customer).start()
        self.subscribe_customer = mock.patch(self._subscribe_customer).start()

    def tearDown(self):
        mock.patch.stopall()
        self.new_cursors.__exit__(None, None, None)
        self.txn.stop()

    def _simulate_holder_change(self, cursor, uid, request_id, context=None):
        self._simulation_savepoint += 1
        savepoint = "holder_change_simulation_{}".format(
            self._simulation_savepoint
        )
        self.raw_cursor.savepoint(savepoint)
        try:
            return self._original_simulate_holder_change(
                self.raw_cursor, uid, request_id, context=context
            )
        finally:
            self.raw_cursor.rollback(savepoint)

    def _create_report(self, cursor, uid, ids, data, context=None):
        return b"%PDF-document", "pdf"

    def _create_html_report(self, cursor, uid, ids, data, report_values, context=None):
        return "<html>{}</html>".format(
            context[holder_change_reports.CARD_PLACEHOLDER_CONTEXT]
        )

    def test_create_request_resolves_active_contract(self):
        result = self.www_obj.create_request(
            self.cursor, self.uid, self.payload()
        )

        self.assertTrue(result["success"], result)
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["contract_pdf", "mandate_pdf", "polissa_id", "owner_change_type", "state"],
        )
        self.assertEqual(request["polissa_id"][0], self.polissa_id)
        self.assertEqual(request["owner_change_type"], "T")
        self.assertEqual(request["state"], "awaiting_signature")
        self.assertTrue(request["contract_pdf"])
        self.assertTrue(request["mandate_pdf"])
        self.assertEqual(
            [
                call[0][0]
                for call in self.local_service.call_args_list
                if call[0][0].startswith("report.")
            ],
            [
                "report.giscedata.polissa.contract.summary.full",
                "report.report_mandato",
            ],
        )

    def test_create_request_persists_attachments_outside_payload(self):
        payload = self.payload()
        payload["especial_cases"]["reason_death"] = True
        payload["attachments"] = [{
            "filename": "death-certificate.pdf",
            "category": "holder_change_death",
            "datas": "JVBERi0xLjQ=",
        }]

        result = self.www_obj.create_request(self.cursor, self.uid, payload)

        self.assertTrue(result["success"], result)
        attachment_obj = self.openerp.pool.get("ir.attachment")
        attachment_ids = attachment_obj.search(
            self.cursor,
            self.uid,
            [
                ("res_model", "=", "som.holder.change.request"),
                ("res_id", "=", result["request_id"]),
            ],
        )
        self.assertEqual(len(attachment_ids), 1)
        attachment = attachment_obj.read(
            self.cursor, self.uid, attachment_ids[0], ["datas_fname", "category_id"]
        )
        self.assertEqual(attachment["datas_fname"], "death-certificate.pdf")
        self.assertEqual(attachment["category_id"][1], "Holder change death certificate")
        request = self.request_obj.read(
            self.cursor, self.uid, result["request_id"], ["payload"]
        )
        self.assertNotIn("datas", request["payload"]["attachments"][0])

    def test_create_request_returns_internal_request_id(self):
        first = self.www_obj.create_request(
            self.cursor, self.uid, self.payload()
        )

        self.assertTrue(first["request_id"])

    def test_create_request_rejects_an_active_request_for_the_same_cups(self):
        first = self.www_obj.create_request(self.cursor, self.uid, self.payload())
        second = self.www_obj.create_request(self.cursor, self.uid, self.payload())

        self.assertTrue(first["success"])
        self.assertFalse(second["success"])
        self.assertEqual(second["code"], "REQUEST_IN_PROGRESS")

    def test_create_request_rejects_same_holder(self):
        payload = self.payload()
        payload["contract_owner"]["vat"] = self.polissa.titular.vat.replace("ES", "")
        payload["contract_owner"].update({
            "proxy_name": "Representant Legal",
            "proxy_vat": "12345678Z",
        })

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "SAME_OWNER")

    def test_create_request_rejects_inactive_new_holder(self):
        payload = self.payload()
        payload["contract_owner"]["vat"] = "11223344B"
        self.openerp.pool.get("res.partner").create(
            self.cursor,
            self.uid,
            {"name": "Inactive holder", "vat": "ES11223344B", "active": False},
            context={"active_test": False},
        )

        result = self.www_obj.create_request(self.cursor, self.uid, payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CUSTOMER_INACTIVE")

    def test_create_request_rejects_non_modifiable_contract(self):
        with mock.patch.object(
            self.www_obj,
            "_check_contract_modifiable",
            return_value=self.www_obj._error("CONTRACT_NOT_MODIFIABLE", "Open ATR"),
        ):
            result = self.www_obj.create_request(self.cursor, self.uid, self.payload())

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CONTRACT_NOT_MODIFIABLE")

    def test_create_request_requires_real_consent(self):
        payload = self.payload()
        payload["sepa_accepted"] = False

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CONSENT_REQUIRED")

    def test_create_request_derives_subrogation_from_special_case(self):
        payload = self.payload()
        payload["especial_cases"]["reason_death"] = True
        payload["attachments"] = [{
            "filename": "death-certificate.pdf",
            "category": "holder_change_death",
            "datas": "JVBERi0xLjQ=",
        }]

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertTrue(result["success"], result)
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["owner_change_type"],
        )
        self.assertEqual(request["owner_change_type"], "S")

    def test_create_request_rejects_inactive_contract(self):
        inactive_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        inactive = self.polissa_obj.browse(self.cursor, self.uid, inactive_id)
        payload = deepcopy(self.payload())
        payload["contract_info"]["cups"] = inactive.cups.name

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CONTRACT_NOT_ACTIVE")

    def test_card_request_waits_for_card_data(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertTrue(result["success"], result)
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["state", "contract_pdf", "mandate_pdf", "report_snapshot"],
        )
        self.assertEqual(request["state"], "awaiting_payment")
        self.assertFalse(request["contract_pdf"])
        self.assertFalse(request["mandate_pdf"])
        self.assertEqual(request["report_snapshot"]["version"], 1)
        self.assertEqual(len(request["report_snapshot"]["documents"]), 2)
        self.simulate_holder_change.assert_called_once()
        self.render_card_reports.assert_not_called()

    def test_card_data_generates_documents_and_waits_for_signature(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )
        card_values = {
            "creditcard_token": "card-token",
            "creditcard_masked_number": "**** **** **** 1234",
            "creditcard_expiry_date": "12/30",
            "creditcard_cof_txnid": "cof-transaction",
        }

        response = self.www_obj.add_payment_card_data(
            self.cursor,
            self.uid,
            result["request_id"],
            payload["contract_info"]["cups"],
            card_values,
        )

        self.assertEqual(response["state"], "awaiting_signature")
        self.simulate_holder_change.assert_called_once()
        self.render_card_reports.assert_called_once()
        self.assertEqual(self.render_card_reports.call_args[0][1], "**** **** **** 1234")
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["state", "contract_pdf", "mandate_pdf"] + list(card_values.keys()),
        )
        self.assertEqual(request["state"], "awaiting_signature")
        self.assertTrue(request["contract_pdf"])
        self.assertFalse(request["mandate_pdf"])
        for field, value in card_values.items():
            self.assertEqual(request[field], value)

    def test_card_data_retries_documents_without_repeating_simulation(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.assertTrue(result["success"], result)
        card_values = {
            "creditcard_token": "card-token",
            "creditcard_masked_number": "**** **** **** 1234",
            "creditcard_expiry_date": "12/30",
            "creditcard_cof_txnid": "cof-transaction",
        }

        self.render_card_reports.side_effect = Exception("PDF rendering failed")
        with mock.patch.object(self.request_obj, "_simulate_holder_change") as simulate:
            with self.assertRaises(Exception):
                self.www_obj.add_payment_card_data(
                    self.cursor,
                    self.uid,
                    result["request_id"],
                    payload["contract_info"]["cups"],
                    card_values,
                )
            simulate.assert_not_called()

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["state", "creditcard_token"],
        )
        self.assertEqual(request["state"], "awaiting_payment")
        self.assertEqual(request["creditcard_token"], card_values["creditcard_token"])

        self.render_card_reports.side_effect = None
        response = self.www_obj.add_payment_card_data(
            self.cursor,
            self.uid,
            result["request_id"],
            payload["contract_info"]["cups"],
            card_values,
        )

        self.assertEqual(response["state"], "awaiting_signature")
        self.simulate_holder_change.assert_called_once()
        self.assertEqual(self.render_card_reports.call_count, 2)

    def test_card_simulation_failure_prevents_payment_state(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        with mock.patch.object(
            self.request_obj, "_run_m1", side_effect=Exception("Invalid M1")
        ):
            response = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.assertEqual(response["code"], "SIMULATION_ERROR")
        self.render_card_reports.assert_not_called()

    def test_card_prepare_reuses_snapshot_before_payment(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.request_obj.prepare(self.cursor, self.uid, result["request_id"])
        self.simulate_holder_change.assert_called_once()

    def test_card_report_preparation_failure_prevents_payment_state(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        with mock.patch.object(
            holder_change_reports, "prepare_snapshot", side_effect=Exception("Invalid report")
        ):
            response = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.assertEqual(response["code"], "SIMULATION_ERROR")
        self.render_card_reports.assert_not_called()

    def test_card_snapshot_uses_real_translated_reports(self):
        self.local_service_patch.stop()
        mock.patch.dict(holder_change_reports.netsvc.SERVICES).start()
        tax_obj = self.openerp.pool.get("account.tax")
        conf_obj = self.openerp.pool.get("res.config")
        for key, tax_name in (
            ("default_iva_21_tax_id", "IVA 21%"),
            ("default_iese_tax_id", "Impuesto especial sobre la electricidad"),
        ):
            tax_id = tax_obj.search(self.cursor, self.uid, [("name", "=", tax_name)])[0]
            conf_obj.set(self.cursor, self.uid, key, tax_id)
        holder_change_reports.PuppeteerParser(
            "report.giscedata.polissa.contract.summary",
            "report.backend.contract.summary",
            "som_polissa_condicions_generals/report/contract_summary_puppeteer.mako",
            params={},
        )
        holder_change_reports.PuppeteerParser(
            "report.giscedata.polissa",
            "report.backend.condicions.particulars",
            "som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako",
            params={},
        )
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True

        def prepare_request(cursor, uid, request_id, context=None):
            self.request_obj.prepare(cursor, uid, request_id, context=context)

        pricelist_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "pricelist_tarifas_electricidad"
        )[1]
        pricelist = self.openerp.pool.get("product.pricelist").browse(
            self.cursor, self.uid, pricelist_id
        )
        mock.patch.dict(config.options, {"default_lang": "ca_ES"}).start()
        with mock.patch.object(self.polissa_obj, "escull_llista_preus", return_value=pricelist):
            with mock.patch.object(
                self.www_obj, "_prepare_stored_request", side_effect=prepare_request
            ):
                with mock.patch.object(holder_change_reports.PuppeteerParser, "render") as render:
                    response = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.assertTrue(response["success"], response)
        render.assert_not_called()
        request = self.request_obj.read(
            self.cursor, self.uid, response["request_id"], ["report_snapshot", "contract_number"]
        )
        snapshot = request["report_snapshot"]
        for document in snapshot["documents"]:
            self.assertIn(snapshot["card_placeholder"], document["html"])
            self.assertIn(request["contract_number"], document["html"])
        self.assertIn("**** **** ****", snapshot["documents"][0]["html"])

    def test_card_data_rejects_missing_snapshot_without_simulating(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.cursor.execute(
            "UPDATE som_holder_change_request SET report_snapshot = NULL WHERE id = %s",
            (result["request_id"],),
        )
        with self.assertRaises(Exception):
            self.www_obj.add_payment_card_data(
                self.cursor, self.uid, result["request_id"], payload["contract_info"]["cups"],
                {"creditcard_token": "token", "creditcard_masked_number": "**** 1234",
                 "creditcard_expiry_date": "12/30", "creditcard_cof_txnid": "cof"},
            )
        self.simulate_holder_change.assert_called_once()
        self.render_card_reports.assert_not_called()

    def test_card_data_rejects_missing_or_repeated_values(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )
        card_values = {
            "creditcard_token": "card-token",
            "creditcard_masked_number": "**** **** **** 1234",
            "creditcard_expiry_date": "12/30",
            "creditcard_cof_txnid": "cof-transaction",
        }

        with self.assertRaises(Exception):
            self.www_obj.add_payment_card_data(
                self.cursor,
                self.uid,
                result["request_id"],
                payload["contract_info"]["cups"],
                {},
            )
        self.www_obj.add_payment_card_data(
            self.cursor,
            self.uid,
            result["request_id"],
            payload["contract_info"]["cups"],
            card_values,
        )
        with self.assertRaises(Exception):
            self.www_obj.add_payment_card_data(
                self.cursor,
                self.uid,
                result["request_id"],
                payload["contract_info"]["cups"],
                card_values,
            )

    def test_card_data_rejects_request_for_a_different_cups(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        result = self.www_obj.create_request(self.cursor, self.uid, payload)

        with self.assertRaises(Exception):
            self.www_obj.add_payment_card_data(
                self.cursor, self.uid, result["request_id"], "ES0000000000000000AA", {}
            )

    def test_card_execute_uses_real_card_after_single_pre_payment_simulation(self):
        payload = self.payload()
        payload["payment_type"] = "tpv"
        del payload["iban"]
        del payload["sepa_accepted"]
        payload["payment_authorization_accepted"] = True
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.www_obj.add_payment_card_data(
            self.cursor, self.uid, result["request_id"], payload["contract_info"]["cups"],
            {"creditcard_token": "real-token", "creditcard_masked_number": "**** 1234",
             "creditcard_expiry_date": "12/30", "creditcard_cof_txnid": "real-cof"},
        )
        self.queue_request(result["request_id"])
        execution = self.request_obj.execute(self.cursor, self.uid, result["request_id"])
        contract = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertEqual(contract.creditcard.token, "real-token")
        self.assertEqual(contract.creditcard.masked_number, "**** 1234")
        self.assertEqual(contract.creditcard.partner_id.id, contract.titular.id)
        self.assertEqual(contract.tipo_pago.code, "COBRAMENT_RECURRENT_TARGETA")
        request = self.request_obj.browse(self.cursor, self.uid, result["request_id"])
        self.assertEqual(contract.name, request.contract_number)
        self.simulate_holder_change.assert_called_once()
        self.render_card_reports.assert_called_once()

    def test_sign_request_keeps_process_after_url_wait_failure(self):
        payload = self.payload()
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        process_obj = self.openerp.pool.get("giscedata.signatura.process")
        lang_obj = self.openerp.pool.get("res.lang")
        lang_ids = lang_obj.search(
            self.cursor, self.uid, [("code", "=", payload["contract_owner"]["lang"])]
        )
        if not lang_ids:
            lang_obj.create(
                self.cursor,
                self.uid,
                {"name": "Català", "code": payload["contract_owner"]["lang"]},
            )

        with mock.patch.object(process_obj, "start", return_value=True):
            with mock.patch.object(
                self.www_obj,
                "_wait_for_signature_url",
                side_effect=Exception("Signature URL timed out"),
            ) as wait_for_signature_url:
                with self.assertRaises(Exception) as raised:
                    self.www_obj.sign_request(
                        self.cursor,
                        self.uid,
                        result["request_id"],
                        payload["contract_info"]["cups"],
                    )
        self.assertTrue(wait_for_signature_url.called, raised.exception)

        self.cursor.rollback()
        with pooler.get_db(self.cursor.dbname).cursor() as verification_cursor:
            request = self.request_obj.read(
                verification_cursor,
                self.uid,
                result["request_id"],
                ["signature_process_id"],
            )
        self.assertTrue(request["signature_process_id"])
        process = process_obj.read(
            self.cursor,
            self.uid,
            request["signature_process_id"][0],
            ["template_id", "template_res_id"],
        )
        template_id = self.imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "som_holder_change",
            "email_signature_process_holder_change",
        )[1]
        self.assertEqual(process["template_id"][0], template_id)
        self.assertEqual(process["template_res_id"], result["request_id"])

    def test_sign_request_retries_process_after_start_failure(self):
        payload = self.payload()
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        process_obj = self.openerp.pool.get("giscedata.signatura.process")
        lang_obj = self.openerp.pool.get("res.lang")
        signature_url = "https://app.signaturit.com/document/signature"
        lang_ids = lang_obj.search(
            self.cursor, self.uid, [("code", "=", payload["contract_owner"]["lang"])]
        )
        if not lang_ids:
            lang_obj.create(
                self.cursor,
                self.uid,
                {"name": "Català", "code": payload["contract_owner"]["lang"]},
            )
        request = self.request_obj.browse(
            self.cursor, self.uid, result["request_id"]
        )
        process_id = process_obj.create(
            self.cursor,
            self.uid,
            self.www_obj._signature_process_values(self.cursor, self.uid, request),
        )
        self.request_obj.write(
            self.cursor,
            self.uid,
            [result["request_id"]],
            {"signature_process_id": process_id},
        )

        with mock.patch.object(
            process_obj,
            "start",
            side_effect=[Exception("Provider unavailable"), True],
        ) as start:
            with mock.patch.object(
                self.www_obj,
                "_wait_for_signature_url",
                return_value=signature_url,
            ) as wait_for_signature_url:
                with self.assertRaises(Exception):
                    self.www_obj.sign_request(
                        self.cursor,
                        self.uid,
                        result["request_id"],
                        payload["contract_info"]["cups"],
                    )
                response = self.www_obj.sign_request(
                    self.cursor,
                    self.uid,
                    result["request_id"],
                    payload["contract_info"]["cups"],
                )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["signature_process_id"],
        )
        self.assertEqual(request["signature_process_id"][0], process_id)
        self.assertEqual(start.call_count, 2)
        self.assertTrue(wait_for_signature_url.called)
        self.assertEqual(
            response["url"], "https://sign-app.signaturit.com/v1/ca/signature"
        )

    def test_sign_request_does_not_start_if_process_association_fails(self):
        payload = self.payload()
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        process_obj = self.openerp.pool.get("giscedata.signatura.process")

        with mock.patch.object(process_obj, "create", return_value=42) as create:
            with mock.patch.object(
                self.request_obj,
                "write",
                side_effect=Exception("Association failed"),
            ) as write:
                with mock.patch.object(process_obj, "start") as start:
                    with self.assertRaises(Exception):
                        self.www_obj.sign_request(
                            self.cursor,
                            self.uid,
                            result["request_id"],
                            payload["contract_info"]["cups"],
                        )

        self.assertIs(create.call_args[0][0], write.call_args[0][0])
        start.assert_not_called()

    def test_simulation_uses_dry_run_context_without_mutating_caller_context(self):
        caller_context = {"is_dry_run": False, "caller_marker": True}

        with mock.patch.object(
            self.request_obj,
            "_run_holder_change",
            wraps=self.request_obj._run_holder_change,
        ) as run_holder_change:
            result = self.www_obj.create_request(
                self.cursor, self.uid, self.payload(), context=caller_context
            )

        self.assertTrue(result["success"], result)
        run_holder_change.assert_called_once()
        simulation_context = run_holder_change.call_args[1]["context"]
        self.assertTrue(run_holder_change.call_args[1]["temporary"])
        self.assertTrue(simulation_context["is_dry_run"])
        self.assertNotIn("in_rollback_transaction", simulation_context)
        self.assertEqual(
            caller_context, {"is_dry_run": False, "caller_marker": True}
        )

    def test_simulation_only_persists_reserved_references(self):
        partner_obj = self.openerp.pool.get("res.partner")
        bank_obj = self.openerp.pool.get("res.partner.bank")
        mandate_obj = self.openerp.pool.get("payment.mandate")
        switching_obj = self.openerp.pool.get("giscedata.switching")
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id, {"donatiu": False}
        )
        old_polissa = self.polissa_obj.read(
            self.cursor, self.uid, self.polissa_id,
            ["donatiu", "no_estimable", "observacions", "observacions_estimacio"],
        )
        vat = "ES12345678Z"
        iban = self.payload()["iban"]
        counts_before = {
            "partner": partner_obj.search_count(
                self.cursor, self.uid, [("vat", "=", vat)]
            ),
            "bank": bank_obj.search_count(
                self.cursor, self.uid, [("iban", "=", iban)]
            ),
            "switching": switching_obj.search_count(self.cursor, self.uid, []),
        }

        result = self.www_obj.create_request(
            self.cursor, self.uid, self.payload()
        )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["contract_number", "mandate_number"],
        )
        self.assertTrue(request["contract_number"])
        self.assertTrue(request["mandate_number"])
        self.assertEqual(
            partner_obj.search_count(self.cursor, self.uid, [("vat", "=", vat)]),
            counts_before["partner"],
        )
        self.assertEqual(
            bank_obj.search_count(self.cursor, self.uid, [("iban", "=", iban)]),
            counts_before["bank"],
        )
        self.assertEqual(
            mandate_obj.search_count(
                self.cursor, self.uid, [("name", "=", request["mandate_number"])]
            ),
            0,
        )
        self.assertEqual(
            switching_obj.search_count(self.cursor, self.uid, []),
            counts_before["switching"],
        )
        self.assertFalse(self.polissa_obj.search(
            self.cursor, self.uid, [("name", "=", request["contract_number"])]
        ))
        self.assertEqual(
            self.polissa_obj.read(
                self.cursor, self.uid, self.polissa_id,
                ["donatiu", "no_estimable", "observacions", "observacions_estimacio"],
            ),
            old_polissa,
        )

    def test_execute_completes_once_without_duplicate_m1(self):
        payload = self.payload()
        payload["contract_owner"]["vat"] = "98765432M"
        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )
        self.queue_request(result["request_id"])

        first_result = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )
        second_result = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        self.assertEqual(first_result, second_result)
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["state", "attempt_count", "switching_id", "result_polissa_id"],
        )
        self.assertEqual(request["state"], "completed")
        self.assertEqual(request["attempt_count"], 1)
        self.assertEqual(request["switching_id"][0], first_result["switching_id"])
        self.assertEqual(
            request["result_polissa_id"][0], first_result["result_polissa_id"]
        )
        self.assertEqual(self.send_mail.call_count, 3)
        self.assertEqual(self.send_mail.call_args_list[0][0][2:4], (
            "giscedata_switching", "notification_atr_M1_01"
        ))
        self.assertEqual(self.send_mail.call_args_list[1][0][2:4], (
            "som_switching", "email_validacio_dades_canvi_titular"
        ))
        self.assertEqual(self.send_mail.call_args_list[2][0][2:4], (
            "som_polissa_soci", "nou_soci_mail_webforms"
        ))
        switching = self.openerp.pool.get("giscedata.switching").browse(
            self.cursor, self.uid, first_result["switching_id"]
        )
        self.assertEqual(switching.state, "open")
        self.assertEqual(switching.proces_id.name, "M1")
        self.assertEqual(switching.get_pas().sollicitudadm, "S")
        self.assertEqual(switching.get_pas().canvi_titular, "T")
        result_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, first_result["result_polissa_id"]
        )
        self.assertTrue(result_polissa.donatiu)
        invoice_number = "QUOTA-SOCIA-CANVI-TITULAR-{}".format(result["request_id"])
        invoice_obj = self.openerp.pool.get("account.invoice")
        invoice_ids = invoice_obj.search(
            self.cursor, self.uid,
            [("partner_id", "=", result_polissa.titular.id), ("number", "=", invoice_number)],
        )
        self.assertEqual(len(invoice_ids), 1)
        invoice = invoice_obj.browse(self.cursor, self.uid, invoice_ids[0])
        self.assertEqual(invoice.state, "draft")
        self.assertFalse(invoice.sii_to_send)
        self.assertEqual(invoice.mandate_id.payment_type, "one_payment")
        self.assertEqual(
            invoice.mandate_id.reference,
            "res.partner,{}".format(result_polissa.titular.id),
        )
        self.assertEqual(switching.get_pas().activacio_cicle, "L")
        self.assertEqual(switching.get_pas().cont_nom, "Maria Nova Titular")
        self.assertEqual(switching.get_pas().cont_telefons[0].numero, "600000000")
        result_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, first_result["result_polissa_id"]
        )
        self.assertTrue(result_polissa.data_firma_contracte)
        old_polissa = self.openerp.pool.get("giscedata.polissa").browse(
            self.cursor, self.uid, self.polissa_id
        )
        self.assertIn("Canvi de titular", old_polissa.observacions_estimacio)
        self.assertTrue(old_polissa.no_estimable)
        self.assertIn("Nou Titular: Nova Titular, Maria", old_polissa.observacions)
        self.assertIn("contract_owner", switching.user_observations)
        self.assertNotIn("JVBERi0xLjQ", switching.user_observations)

    def test_transfer_can_disable_inherited_voluntary_donation(self):
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id, {"donatiu": True}
        )
        payload = self.payload()
        payload["donation"] = False
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.assertTrue(result["success"], result)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        result_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        old_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, self.polissa_id
        )
        self.assertFalse(result_polissa.donatiu)
        self.assertTrue(old_polissa.donatiu)

    def test_subrogation_creates_draft_m1(self):
        payload = self.payload()
        payload["especial_cases"].update({"reason_death": True})
        payload["attachments"] = [
            {
                "filename": "death-certificate.pdf",
                "category": "holder_change_death",
                "datas": "JVBERi0xLjQ=",
            },
            {
                "filename": "death-certificate-2.pdf",
                "category": "holder_change_death",
                "datas": "JVBERi0xLjQy",
            },
        ]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.assertTrue(result["success"], result)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        switching = self.openerp.pool.get("giscedata.switching").browse(
            self.cursor, self.uid, execution["switching_id"]
        )
        self.assertEqual(switching.state, "draft")
        self.assertEqual(switching.get_pas().sollicitudadm, "S")
        self.assertEqual(switching.get_pas().canvi_titular, "S")
        result_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertTrue(result_polissa.donatiu)
        self.assertEqual(self.send_mail.call_args_list[0][0][2:4], (
            "som_polissa_condicions_generals", "notification_atr_M1_01_SS"
        ))

    def test_execute_uses_new_holder_language_and_address(self):
        payload = self.payload()
        payload["contract_owner"]["vat"] = "76543210S"
        payload["contract_owner"]["lang"] = self.polissa.titular.lang
        payload["iban"] = "es91 2100-0418.4502/0005 1332"
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.assertTrue(result["success"], result)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertEqual(polissa.titular.lang, payload["contract_owner"]["lang"])
        self.assertEqual(polissa.titular.name, "Nova Titular, Maria")
        self.assertEqual(
            polissa.direccio_pagament.nv,
            payload["contract_owner"]["address"]["street"],
        )
        self.assertEqual(
            polissa.direccio_pagament.pnp,
            payload["contract_owner"]["address"]["number"],
        )
        self.assertEqual(
            polissa.direccio_pagament.state_id.id,
            payload["contract_owner"]["address"]["state_id"],
        )
        self.assertEqual(
            polissa.direccio_pagament.id_municipi.id,
            payload["contract_owner"]["address"]["city_id"],
        )
        self.assertEqual(polissa.direccio_pagament.country_id.code, "ES")
        self.assertEqual(
            polissa.direccio_pagament.id_poblacio.municipi_id.id,
            payload["contract_owner"]["address"]["city_id"],
        )
        self.assertEqual(polissa.bank.iban, "ES9121000418450200051332")
        self.assertEqual(
            polissa.direccio_notificacio.id, polissa.direccio_pagament.id
        )

    def test_execute_stores_legal_representative_for_a_new_company(self):
        payload = self.payload()
        payload["contract_owner"].update({
            "name": "Empresa Nova SA",
            "vat": "A08015497",
            "proxy_name": "Maria Representant",
            "proxy_vat": "12345678Z",
        })
        del payload["contract_owner"]["surname"]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        holder = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        ).titular
        self.assertEqual(holder.name, payload["contract_owner"]["name"])
        self.assertIn("Maria Representant", holder.comment)
        self.assertIn("12345678Z", holder.comment)

    def test_execute_assigns_linked_member_to_result_contract(self):
        payload = self.payload()
        payload["linked_member"] = "sponsored"
        payload["linked_member_info"] = {
            "vat": "97053918J",
            "code": "202129",
        }
        linked_partner_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_soci"
        )[1]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertEqual(polissa.soci.id, linked_partner_id)

    def test_execute_turns_new_holder_into_member(self):
        result = self.www_obj.create_request(self.cursor, self.uid, self.payload())
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertEqual(polissa.soci.id, polissa.titular.id)

    def test_execute_assigns_ct_ss_member_and_category_without_member(self):
        payload = self.payload()
        payload["linked_member"] = "without_member"
        ct_ss_member_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_soci_ct"
        )[1]
        category_id = self.imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "som_polissa_soci",
            "origen_ct_sense_socia_category",
        )[1]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertEqual(polissa.soci.id, ct_ss_member_id)
        self.assertIn(category_id, polissa.category_id.ids)

    def test_subrogation_assigns_ct_ss_member_and_category_without_member(self):
        payload = self.payload()
        payload["linked_member"] = "without_member"
        payload["especial_cases"].update({"reason_death": True})
        payload["attachments"] = [{
            "filename": "death-certificate.pdf",
            "category": "holder_change_death",
            "datas": "JVBERi0xLjQ=",
        }]
        ct_ss_member_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "res_partner_soci_ct"
        )[1]
        category_id = self.imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "som_polissa_soci",
            "origen_ct_sense_socia_category",
        )[1]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertEqual(polissa.soci.id, ct_ss_member_id)
        self.assertIn(category_id, polissa.category_id.ids)

    def test_execute_copies_death_certificate_to_result_contract(self):
        payload = self.payload()
        payload["especial_cases"].update({"reason_death": True})
        payload["attachments"] = [
            {
                "filename": "death-certificate.pdf",
                "category": "holder_change_death",
                "datas": "JVBERi0xLjQ=",
            },
            {
                "filename": "death-certificate-2.pdf",
                "category": "holder_change_death",
                "datas": "JVBERi0xLjQy",
            },
        ]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])

        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )

        attachment_ids = self.openerp.pool.get("ir.attachment").search(
            self.cursor,
            self.uid,
            [
                ("res_model", "=", "giscedata.polissa"),
                ("res_id", "=", execution["result_polissa_id"]),
                ("description", "=", "Certificat defunció"),
            ],
        )
        self.assertEqual(len(attachment_ids), 2)
        attachments = self.openerp.pool.get("ir.attachment").read(
            self.cursor, self.uid, attachment_ids, ["datas_fname", "datas"]
        )
        self.assertEqual(
            sorted(attachment["datas_fname"] for attachment in attachments),
            ["death-certificate-2.pdf", "death-certificate.pdf"],
        )
        self.assertEqual(
            sorted(attachment["datas"] for attachment in attachments),
            ["JVBERi0xLjQ=", "JVBERi0xLjQy"],
        )

        request = self.request_obj.browse(
            self.cursor, self.uid, result["request_id"]
        )
        self.request_obj._apply_special_documents(
            self.cursor,
            self.uid,
            request,
            self.polissa_obj.browse(
                self.cursor, self.uid, execution["result_polissa_id"]
            ).titular.id,
            execution["result_polissa_id"],
        )
        self.assertEqual(len(self.openerp.pool.get("ir.attachment").search(
            self.cursor,
            self.uid,
            [
                ("res_model", "=", "giscedata.polissa"),
                ("res_id", "=", execution["result_polissa_id"]),
                ("description", "=", "Certificat defunció"),
            ],
        )), 2)

    def test_execute_copies_merge_certificate_to_result_contract(self):
        payload = self.payload()
        payload["especial_cases"].update({"reason_merge": True})
        payload["attachments"] = [{
            "filename": "merge-certificate.pdf",
            "category": "holder_change_merge",
            "datas": "JVBERi0xLjQ=",
        }]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])
        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )
        attachment_ids = self.openerp.pool.get("ir.attachment").search(
            self.cursor,
            self.uid,
            [
                ("res_model", "=", "giscedata.polissa"),
                ("res_id", "=", execution["result_polissa_id"]),
                ("description", "=", "Certificat fusió"),
            ],
        )
        self.assertEqual(len(attachment_ids), 1)

    def test_execute_creates_electrodependency_document_and_nocutoff(self):
        payload = self.payload()
        payload["especial_cases"].update({"reason_electrodep": True})
        payload["attachments"] = [
            {
                "filename": "medical-certificate.pdf",
                "category": "holder_change_medical",
                "datas": "JVBERi0xLjQ=",
            },
            {
                "filename": "resident-certificate.pdf",
                "category": "holder_change_medical",
                "datas": "JVBERi0xLjQy",
            },
        ]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])
        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )
        partner_ids = self.openerp.pool.get("res.partner").search(
            self.cursor, self.uid,
            [("vat", "=", "ES" + payload["contract_owner"]["vat"])],
        )
        document_ids = self.openerp.pool.get("som.documents.sensibles").search(
            self.cursor,
            self.uid,
            [("partner_id", "=", partner_ids[0])],
        )
        self.assertEqual(len(document_ids), 1)
        attachment_ids = self.openerp.pool.get("ir.attachment").search(
            self.cursor,
            self.uid,
            [
                ("res_model", "=", "som.documents.sensibles"),
                ("res_id", "=", document_ids[0]),
                ("description", "=", "Justificant mèdic"),
            ],
        )
        self.assertEqual(len(attachment_ids), 2)
        result_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        self.assertTrue(result_polissa.nocutoff)

    def test_execute_reuses_existing_electrodependency_document(self):
        payload = self.payload()
        payload["contract_owner"]["vat"] = "87654321X"
        payload["especial_cases"].update({"reason_electrodep": True})
        payload["attachments"] = [{
            "filename": "medical-certificate.pdf",
            "category": "holder_change_medical",
            "datas": "JVBERi0xLjQ=",
        }]
        partner_obj = self.openerp.pool.get("res.partner")
        partner_ids = partner_obj.search(
            self.cursor, self.uid,
            [("vat", "=", "ES" + payload["contract_owner"]["vat"])],
        )
        partner_id = partner_ids[0] if partner_ids else partner_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "Existing holder",
                "vat": "ES" + payload["contract_owner"]["vat"],
            },
        )
        category_id = self.imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "som_documents_sensibles",
            "documents_sensibles_category_electrodependent",
        )[1]
        document_obj = self.openerp.pool.get("som.documents.sensibles")
        document_ids = document_obj.search(
            self.cursor,
            self.uid,
            [("partner_id", "=", partner_id), ("categoria", "=", category_id)],
        )
        document_id = document_ids[0] if document_ids else document_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "Existing sensitive document",
                "data_recepcio": "2020-01-01",
                "darrera_data_valida": "2020-01-01",
                "partner_id": partner_id,
                "categoria": category_id,
            },
        )
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])

        self.request_obj.execute(self.cursor, self.uid, result["request_id"])

        document_ids = document_obj.search(
            self.cursor, self.uid, [("partner_id", "=", partner_id)]
        )
        self.assertEqual(document_ids, [document_id])
        self.assertEqual(
            document_obj.read(self.cursor, self.uid, document_id, ["categoria"])["categoria"][0],
            category_id,
        )

    def test_execute_ignores_sensitive_documents_of_other_categories(self):
        payload = self.payload()
        payload["contract_owner"]["vat"] = "24681357B"
        payload["especial_cases"].update({"reason_electrodep": True})
        payload["attachments"] = [{
            "filename": "medical-certificate.pdf",
            "category": "holder_change_medical",
            "datas": "JVBERi0xLjQ=",
        }]
        partner_obj = self.openerp.pool.get("res.partner")
        partner_ids = partner_obj.search(
            self.cursor, self.uid,
            [("vat", "=", "ES" + payload["contract_owner"]["vat"])],
        )
        partner_id = partner_ids[0] if partner_ids else partner_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "Holder with other document",
                "vat": "ES" + payload["contract_owner"]["vat"],
            },
        )
        document_obj = self.openerp.pool.get("som.documents.sensibles")
        other_category_id = self.imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "som_documents_sensibles",
            "documents_sensibles_category_other",
        )[1]
        other_document_ids = document_obj.search(
            self.cursor,
            self.uid,
            [("partner_id", "=", partner_id), ("categoria", "=", other_category_id)],
        )
        if not other_document_ids:
            document_obj.create(
                self.cursor,
                self.uid,
                {
                    "name": "Other sensitive document",
                    "data_recepcio": "2020-01-01",
                    "darrera_data_valida": "2020-01-01",
                    "partner_id": partner_id,
                    "categoria": other_category_id,
                },
            )

        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.queue_request(result["request_id"])
        self.request_obj.execute(self.cursor, self.uid, result["request_id"])

        electro_category_id = self.imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "som_documents_sensibles",
            "documents_sensibles_category_electrodependent",
        )[1]
        electro_document_ids = document_obj.search(
            self.cursor,
            self.uid,
            [("partner_id", "=", partner_id), ("categoria", "=", electro_category_id)],
        )
        self.assertEqual(len(electro_document_ids), 1)

    def payload(self):
        return {
            "payment_type": "remesa",
            "iban": "ES9121000418450200051332",
            "sepa_accepted": True,
            "donation": True,
            "contract_info": {"cups": self.polissa.cups.name},
            "privacy_conditions": True,
            "general_contract_terms_accepted": True,
            "linked_member": "new_member",
            "especial_cases": {
                "reason_death": False,
                "reason_merge": False,
                "reason_electrodep": False,
            },
            "contract_owner": {
                "name": "Maria",
                "surname": "Nova Titular",
                "vat": "12345678Z",
                "address": {
                    "street": "Carrer Nou",
                    "number": "1",
                    "postal_code": "17001",
                    "state_id": self.polissa.cups.id_municipi.state.id,
                    "city_id": self.polissa.cups.id_municipi.id,
                },
                "email": "maria@example.com",
                "phone": "600000000",
                "lang": "ca_ES",
            },
        }

    def queue_request(self, request_id):
        self.request_obj.write(
            self.cursor, self.uid, [request_id], {"state": "queued"}
        )
