# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from osv import osv

import mock
from poweremail.poweremail_template import get_value
from tools.translate import trans_load

from destral import testing
from destral.transaction import Transaction


class TestHolderChangeRequest(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

    def tearDown(self):
        self.txn.stop()

    def test_create_sets_received_state(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            request_id,
            ["state"],
        )

        self.assertEqual(request["state"], "received")

    def test_write_rejects_changes_to_request_identity(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        for values in (
            {"payload": {"contract_owner": {"vat": "B12345678"}}},
            {"polissa_id": self.polissa_id},
            {"cups": "ES00000000000000000000"},
            {"owner_change_type": "S"},
            {"report_snapshot": {"version": 1}},
        ):
            with self.assertRaises(osv.except_osv):
                self.request_obj.write(
                    self.cursor, self.uid, [request_id], values
                )

    def test_write_allows_workflow_fields(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )

        self.request_obj.write(
            self.cursor,
            self.uid,
            [request_id],
            {"state": "validation_error", "error_message": "Invalid IBAN"},
        )

        request = self.request_obj.read(
            self.cursor,
            self.uid,
            request_id,
            ["state", "error_message"],
        )
        self.assertEqual(request["state"], "validation_error")
        self.assertEqual(request["error_message"], "Invalid IBAN")

    def test_send_sign_email_reuses_pending_signature(self):
        signature_obj = self.openerp.pool.get("giscedata.signatura.process")
        mailbox_obj = self.openerp.pool.get("poweremail.mailbox")
        context = {"lang": "ca_ES"}
        for status in ("wait", "doing"):
            signature = mock.Mock(id=42, status=status, signature_url="https://sign.example/42")
            signature.template_id.id = 7
            request = mock.Mock(signature_process_id=signature)
            with mock.patch.object(self.request_obj, "browse", return_value=request):
                with mock.patch.object(signature_obj, "send_poweremail") as generate:
                    with mock.patch.object(signature_obj, "create") as create:
                        with mock.patch.object(mailbox_obj, "search", return_value=[9]) as search:
                            with mock.patch.object(mailbox_obj, "send_this_mail") as send:
                                self.assertTrue(self.request_obj.send_sign_email(
                                    self.cursor, self.uid, [1], context=context
                                ))
            generate.assert_called_once_with(self.cursor, self.uid, [42], context=context)
            create.assert_not_called()
            search.assert_called_once_with(
                self.cursor, self.uid,
                [("reference", "=", "giscedata.signatura.process,42"),
                 ("template_id", "=", 7), ("folder", "=", "outbox")],
                context=context,
            )
            send.assert_called_once_with(self.cursor, self.uid, [9], context=context)
        self.assertEqual(context, {"lang": "ca_ES"})

    def test_check_signature_and_execute_uses_existing_queue_endpoint(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )
        context = {"lang": "ca_ES"}
        www_obj = self.openerp.pool.get("som.holder.change.www")
        with mock.patch.object(www_obj, "execute_request") as enqueue:
            self.assertTrue(self.request_obj.check_signature_and_execute(
                self.cursor, self.uid, [request_id], context=context
            ))
        enqueue.assert_called_once_with(
            self.cursor, self.uid, request_id, self.request_values()["cups"], context=context
        )

    def test_check_signature_and_execute_rejects_missing_signature(self):
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )
        www_obj = self.openerp.pool.get("som.holder.change.www")
        with mock.patch.object(www_obj, "execute_request_async") as enqueue:
            with self.assertRaises(osv.except_osv):
                self.request_obj.check_signature_and_execute(
                    self.cursor, self.uid, [request_id]
                )
        enqueue.assert_not_called()

    def test_send_sign_email_rejects_missing_or_unavailable_signature(self):
        signature_obj = self.openerp.pool.get("giscedata.signatura.process")
        mailbox_obj = self.openerp.pool.get("poweremail.mailbox")
        signatures = [False, mock.Mock(status="wait", signature_url=False)]
        signatures.extend(mock.Mock(status=status) for status in (
            "unsend", "completed", "canceled", "expired", "declined", "error",
        ))
        with mock.patch.object(signature_obj, "send_poweremail") as generate:
            with mock.patch.object(mailbox_obj, "send_this_mail") as send:
                for signature in signatures:
                    request = mock.Mock(signature_process_id=signature)
                    with mock.patch.object(self.request_obj, "browse", return_value=request):
                        with self.assertRaises(osv.except_osv):
                            self.request_obj.send_sign_email(self.cursor, self.uid, [1])
        generate.assert_not_called()
        send.assert_not_called()

    def test_signature_email_template_renders_link_and_language(self):
        template_obj = self.openerp.pool.get("poweremail.templates")
        template_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_holder_change", "email_signature_process_holder_change"
        )[1]
        request_id = self.request_obj.create(
            self.cursor, self.uid, self.request_values()
        )
        for signature_lang, email_lang in (
            ("ca_ES", "ca_ES"),
            ("es_ES", "es_ES"),
            ("en_US", "ca_ES"),
        ):
            lang_obj = self.openerp.pool.get("res.lang")
            if not lang_obj.search(self.cursor, self.uid, [("code", "=", email_lang)]):
                lang_obj.create(
                    self.cursor, self.uid, {"name": email_lang, "code": email_lang}
                )
            trans_load(
                self.cursor,
                os.path.join(os.path.dirname(__file__), "..", "i18n", email_lang + ".po"),
                email_lang, verbose=False,
            )
            context = {
                "lang": email_lang,
                "signature": {
                    "signature_url": "https://sign.example/42", "lang": signature_lang,
                },
            }
            template = template_obj.browse(
                self.cursor, self.uid, template_id, context=context
            )
            body = get_value(
                self.cursor, self.uid, request_id,
                message=template.def_body_text, template=template, context=context,
            )
            self.assertIn("https://sign.example/42", body)
            self.assertEqual(get_value(
                self.cursor, self.uid, request_id,
                message=template.lang, template=template, context=context,
            ), email_lang)

    def request_values(self, **values):
        result = {
            "polissa_id": self.polissa_id,
            "cups": "ES12345678901234567890",
            "owner_change_type": "T",
            "payload": {
                "contract_owner": {"vat": "12345678Z", "name": "New holder"},
                "iban": "ES9121000418450200051332",
            },
        }
        result.update(values)
        return result


class TestHolderChangeAddress(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestHolderChangeAddress, self).setUp()
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        polissa_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.polissa = self.openerp.pool.get("giscedata.polissa").browse(
            self.cursor, self.uid, polissa_id
        )

    def test_new_card_holder_address_uses_state_country_without_iban(self):
        self._check_new_holder_address_country({"payment_type": "tpv"})

    def test_new_holder_address_country_does_not_follow_foreign_iban(self):
        self._check_new_holder_address_country({
            "payment_type": "remesa", "iban": "DE89370400440532013000",
        })

    def _check_new_holder_address_country(self, payment_values):
        payload = {
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
            },
        }
        payload.update(payment_values)
        partner_id = self.openerp.pool.get("res.partner").create(
            self.cursor, self.uid, {"name": "New address holder", "vat": "ES76543210S"}
        )
        request_id = self.request_obj.create(
            self.cursor, self.uid,
            {"polissa_id": self.polissa.id, "cups": self.polissa.cups.name,
             "owner_change_type": "T", "payload": payload},
        )
        request = self.request_obj.browse(self.cursor, self.uid, request_id)
        address_id = self.request_obj._create_holder_address(
            self.cursor, self.uid, request, partner_id
        )
        address = self.openerp.pool.get("res.partner.address").browse(
            self.cursor, self.uid, address_id
        )
        self.assertEqual(address.country_id.code, "ES")
        self.assertEqual(address.country_id.id, address.state_id.country_id.id)
