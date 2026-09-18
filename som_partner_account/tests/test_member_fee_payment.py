# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction


class TestMemberFeePayment(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.partner_o = self.model("res.partner")
        self.invoice_o = self.model("account.invoice")
        self.mandate_o = self.model("payment.mandate")
        self.bank_o = self.model("res.partner.bank")
        self.payment_mode_o = self.model("payment.mode")
        self.payment_type_o = self.model("payment.type")
        self.journal_o = self.model("account.journal")
        self.account_o = self.model("account.account")
        self.config_o = self.model("res.config")
        self.request_link_o = self.model("res.request.link")
        self.imd_o = self.model("ir.model.data")
        self.partner_id = self.imd_o.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_c2c"
        )[1]
        self.iban = "ES77 1234 1234 1612 3456 7890"
        if not self.request_link_o.search(
                self.cursor, self.uid, [("object", "=", "res.partner")]):
            self.request_link_o.create(self.cursor, self.uid, {
                "name": "Partner",
                "object": "res.partner",
            })
        self._create_member_fee_configuration()
        self.bank_o.create(self.cursor, self.uid, {
            "partner_id": self.partner_id,
            "iban": self.iban.replace(" ", ""),
            "state": "iban",
        })

    def _create_member_fee_configuration(self):
        capital_parent_id = self.account_o.search(
            self.cursor, self.uid, [("code", "=", "100")]
        )[0]
        capital_type_id = self.imd_o.get_object_reference(
            self.cursor, self.uid, "l10n_chart_ES", "capital"
        )[1]
        capital_account_ids = self.account_o.search(
            self.cursor, self.uid, [("code", "=", "100000000000")]
        )
        if not capital_account_ids:
            self.account_o.create(self.cursor, self.uid, {
                "name": "Mandatory social capital",
                "code": "100000000000",
                "type": "other",
                "parent_id": capital_parent_id,
                "user_type": capital_type_id,
            })
        journal_view_id = self.imd_o.get_object_reference(
            self.cursor, self.uid, "account", "account_journal_bank_view"
        )[1]
        sequence_id = self.imd_o.get_object_reference(
            self.cursor, self.uid, "account", "sequence_statement"
        )[1]
        bank_id = self.imd_o.get_object_reference(
            self.cursor, self.uid, "base", "partner_bank"
        )[1]
        journal_ids = self.journal_o.search(
            self.cursor, self.uid, [("code", "=", "SOCIS")]
        )
        journal_id = journal_ids and journal_ids[0] or self.journal_o.create(
            self.cursor, self.uid, {
                "name": "SOCIS",
                "code": "SOCIS",
                "type": "sale",
                "view_id": journal_view_id,
                "sequence_id": sequence_id,
            }
        )
        payment_type_id = self.payment_type_o.search(
            self.cursor, self.uid, [("code", "=", "RECIBO_CSB")]
        )[0]
        payment_mode_ids = self.payment_mode_o.search(
            self.cursor, self.uid, [("name", "=", "QUOTA SOCIS amb Factura")]
        )
        payment_mode_id = payment_mode_ids and payment_mode_ids[0] or self.payment_mode_o.create(
            self.cursor, self.uid, {
                "name": "QUOTA SOCIS amb Factura",
                "type": payment_type_id,
                "journal": journal_id,
                "tipo": "sepa19",
                "nombre": "Som Energia",
                "sufijo": "000",
                "require_bank_account": True,
                "partner_id": 1,
                "bank_id": bank_id,
                "sepa_creditor_code": "ES10000B22350466",
            }
        )
        mode_xml_ids = self.imd_o.search(
            self.cursor, self.uid,
            [("module", "=", "som_partner_account"),
             ("name", "=", "mode_pagament_socis_factura")]
        )
        if not mode_xml_ids:
            self.imd_o.create(self.cursor, self.uid, {
                "module": "som_partner_account",
                "name": "mode_pagament_socis_factura",
                "model": "payment.mode",
                "res_id": payment_mode_id,
                "noupdate": True,
            })
        config_ids = self.config_o.search(
            self.cursor, self.uid, [("name", "=", "socia_member_fee_amount")]
        )
        if not config_ids:
            self.config_o.create(self.cursor, self.uid, {
                "name": "socia_member_fee_amount",
                "value": "100",
                "description": "Member fee amount",
            })

    def tearDown(self):
        self.txn.stop()

    def test_create_member_fee_payment_creates_invoice_and_remittance(self):
        invoice_number = "QUOTA-SOCIA-TEST-1"

        invoice_id = self.partner_o.create_member_fee_payment(
            self.cursor,
            self.uid,
            self.partner_id,
            self.iban,
            "S123456",
            invoice_number,
        )

        invoice = self.invoice_o.browse(self.cursor, self.uid, invoice_id)
        payment_mode_id = self.imd_o.get_object_reference(
            self.cursor, self.uid, "som_partner_account", "mode_pagament_socis_factura"
        )[1]
        mandate_id = self.mandate_o.search(
            self.cursor,
            self.uid,
            [
                ("reference", "=", "res.partner,{}".format(self.partner_id)),
                ("debtor_iban", "=", self.iban.replace(" ", "")),
                ("notes", "=", "QUOTA SOCI"),
            ],
        )[0]
        mandate = self.mandate_o.browse(self.cursor, self.uid, mandate_id)

        self.assertEqual(invoice.number, invoice_number)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.state, "open")
        self.assertFalse(invoice.sii_to_send)
        self.assertEqual(mandate.payment_type, "one_payment")
        self.assertEqual(mandate.debtor_iban, self.iban.replace(" ", ""))
        self.assertEqual(invoice.payment_order_id.mode.id, payment_mode_id)
        self.assertEqual(invoice.payment_order_id.state, "draft")
        self.assertEqual(invoice.payment_order_id.line_ids[0].name, "S123456")
