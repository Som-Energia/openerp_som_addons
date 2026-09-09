# -*- coding: utf-8 -*-
from __future__ import absolute_import

from copy import deepcopy

import mock
from destral import testing
from destral.transaction import Transaction


class TestHolderChangeWww(testing.OOTestCase):

    _local_service = (
        "som_holder_change.models.holder_change_request.netsvc.LocalService"
    )

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.www_obj = self.openerp.pool.get("som.holder.change.www")
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
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
        self.local_service = mock.patch(self._local_service).start()
        self.local_service.return_value.create.side_effect = [
            (b"%PDF-contract", "pdf"),
            (b"%PDF-mandate", "pdf"),
        ]

    def tearDown(self):
        mock.patch.stopall()
        self.txn.stop()

    def payload(self):
        return {
            "payment_method": "bank",
            "payment": {
                "iban": "ES9121000418450200051332",
                "sepa_accepted": True,
                "voluntary_cent": True,
            },
            "supply_point": {
                "cups": self.polissa.cups.name,
                "address": self.polissa.cups.direccio,
            },
            "privacy_policy_accepted": True,
            "terms_accepted": True,
            "member": {
                "invite_token": False,
                "become_member": True,
                "link_member": False,
            },
            "especial_cases": {
                "reason_death": False,
                "reason_merge": False,
                "reason_electrodep": False,
                "attachments": {},
            },
            "holder": {
                "name": "Maria",
                "surname1": "Nova",
                "surname2": "Titular",
                "vat": "12345678Z",
                "address": "Carrer Nou, 1",
                "postal_code": "17001",
                "state": self.polissa.cups.id_municipi.state.id,
                "city": self.polissa.cups.id_municipi.id,
                "email": "maria@example.com",
                "phone1": "600000000",
                "language": "ca_ES",
            },
        }

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

    def test_card_request_waits_for_card_data(self):
        payload = self.payload()
        payload["payment_method"] = "card"
        del payload["payment"]["iban"]
        del payload["payment"]["sepa_accepted"]

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertTrue(result["success"], result)
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["state", "contract_pdf", "mandate_pdf"],
        )
        self.assertEqual(request["state"], "awaiting_payment")
        self.assertTrue(request["contract_pdf"])
        self.assertFalse(request["mandate_pdf"])

    def test_card_data_generates_documents_and_waits_for_signature(self):
        payload = self.payload()
        payload["payment_method"] = "card"
        del payload["payment"]["iban"]
        del payload["payment"]["sepa_accepted"]
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
            self.cursor, self.uid, result["request_id"], card_values
        )

        self.assertEqual(response["state"], "awaiting_signature")
        request = self.request_obj.read(
            self.cursor,
            self.uid,
            result["request_id"],
            ["state", "contract_pdf", "mandate_pdf"] + card_values.keys(),
        )
        self.assertEqual(request["state"], "awaiting_signature")
        self.assertTrue(request["contract_pdf"])
        self.assertFalse(request["mandate_pdf"])
        for field, value in card_values.items():
            self.assertEqual(request[field], value)

    def test_card_data_rejects_missing_or_repeated_values(self):
        payload = self.payload()
        payload["payment_method"] = "card"
        del payload["payment"]["iban"]
        del payload["payment"]["sepa_accepted"]
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
                self.cursor, self.uid, result["request_id"], {}
            )
        self.www_obj.add_payment_card_data(
            self.cursor, self.uid, result["request_id"], card_values
        )
        with self.assertRaises(Exception):
            self.www_obj.add_payment_card_data(
                self.cursor, self.uid, result["request_id"], card_values
            )

    def test_simulation_only_persists_reserved_references(self):
        partner_obj = self.openerp.pool.get("res.partner")
        bank_obj = self.openerp.pool.get("res.partner.bank")
        mandate_obj = self.openerp.pool.get("payment.mandate")
        switching_obj = self.openerp.pool.get("giscedata.switching")
        vat = "ES12345678Z"
        iban = self.payload()["payment"]["iban"]
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

    def test_execute_completes_once_without_duplicate_m1(self):
        result = self.www_obj.create_request(
            self.cursor, self.uid, self.payload()
        )
        self.request_obj.write(
            self.cursor, self.uid, [result["request_id"]], {"state": "queued"}
        )

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

    def test_execute_copies_death_certificate_to_result_contract(self):
        payload = self.payload()
        payload["especial_cases"].update({"reason_death": True})
        payload["attachments"] = [{
            "filename": "death-certificate.pdf",
            "category": "holder_change_death",
            "datas": "JVBERi0xLjQ=",
        }]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.request_obj.write(
            self.cursor, self.uid, [result["request_id"]], {"state": "queued"}
        )

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
        self.assertEqual(len(attachment_ids), 1)

    def test_execute_copies_merge_certificate_to_result_contract(self):
        payload = self.payload()
        payload["especial_cases"].update({"reason_merge": True})
        payload["attachments"] = [{
            "filename": "merge-certificate.pdf",
            "category": "holder_change_merge",
            "datas": "JVBERi0xLjQ=",
        }]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.request_obj.write(
            self.cursor, self.uid, [result["request_id"]], {"state": "queued"}
        )
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
        payload["attachments"] = [{
            "filename": "medical-certificate.pdf",
            "category": "holder_change_medical",
            "datas": "JVBERi0xLjQ=",
        }]
        result = self.www_obj.create_request(self.cursor, self.uid, payload)
        self.request_obj.write(
            self.cursor, self.uid, [result["request_id"]], {"state": "queued"}
        )
        execution = self.request_obj.execute(
            self.cursor, self.uid, result["request_id"]
        )
        result_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, execution["result_polissa_id"]
        )
        document_ids = self.openerp.pool.get("som.documents.sensibles").search(
            self.cursor,
            self.uid,
            [("partner_id", "=", result_polissa.titular.id)],
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
        self.assertEqual(len(attachment_ids), 1)
        self.assertTrue(result_polissa.nocutoff)

    def test_create_request_returns_internal_request_id(self):
        first = self.www_obj.create_request(
            self.cursor, self.uid, self.payload()
        )

        self.assertTrue(first["request_id"])

    def test_create_request_rejects_same_holder(self):
        payload = self.payload()
        payload["holder"]["vat"] = self.polissa.titular.vat.replace("ES", "")
        payload["holder"].update({
            "proxyname": "Representant Legal",
            "proxynif": "12345678Z",
        })

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "SAME_OWNER")

    def test_create_request_requires_real_consent(self):
        payload = self.payload()
        payload["payment"]["sepa_accepted"] = False

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CONSENT_REQUIRED")

    def test_create_request_derives_subrogation_from_special_case(self):
        payload = self.payload()
        payload["especial_cases"].update({
            "reason_death": True,
            "attachments": {"death": "attachment-id"},
        })

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
        payload["supply_point"]["cups"] = inactive.cups.name

        result = self.www_obj.create_request(
            self.cursor, self.uid, payload
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "CONTRACT_NOT_ACTIVE")
