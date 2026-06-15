# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime
from destral.patch import PatchNewCursors
from osv import osv

from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwMemberPayment(BaseSomLeadWwwTest):
    def test_create_lead_defaults_card_recurrent_for_tpv_member_payment(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["payment_type"] = "tpv"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.member_quota_payment_type, "tpv")
        self.assertEqual(lead.billing_payment_method, "card_recurrent")

    def test_create_lead_defaults_remesa_for_remesa_member_payment(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["payment_type"] = "remesa"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.member_quota_payment_type, "remesa")
        self.assertEqual(lead.billing_payment_method, "remesa")

    def test_create_lead_accepts_explicit_tpv_card_recurrent_pair(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "card_recurrent"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.member_quota_payment_type, "tpv")
        self.assertEqual(lead.billing_payment_method, "card_recurrent")

    def test_create_lead_accepts_explicit_remesa_pair(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["payment_type"] = "remesa"
        values["billing_payment_method"] = "remesa"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.member_quota_payment_type, "remesa")
        self.assertEqual(lead.billing_payment_method, "remesa")

    def test_create_lead_rejects_tpv_with_remesa_billing(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["payment_type"] = "tpv"
        values["billing_payment_method"] = "remesa"

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_create_lead_rejects_remesa_with_card_recurrent_billing(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["payment_type"] = "remesa"
        values["billing_payment_method"] = "card_recurrent"

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_create_lead_rejects_card_recurrent_without_payment_type(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        del values["payment_type"]
        values["billing_payment_method"] = "card_recurrent"

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_create_lead_with_remesable_member(self):
        www_lead_o = self.get_model("som.lead.www")
        account_invoice_o = self.get_model("account.invoice")
        lead_o = self.get_model("giscedata.crm.lead")
        mandate_o = self.get_model("payment.mandate")
        ir_model_o = self.get_model("ir.model.data")
        payment_order_o = self.get_model("payment.order")
        wiz_pay_o = self.get_model('pagar.remesa.wizard')
        ir_sequence_o = self.get_model("ir.sequence")

        # Receveivable payment order should have a different prefix
        rec_payment_order_seq_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "account_payment_extension", "seq_rec_payment_order"
        )[1]
        ir_sequence_o.write(
            self.cursor, self.uid, rec_payment_order_seq_id, {'prefix': 'R%(year)s/'})

        values = self._basic_values
        values["payment_type"] = "remesa"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        titular_id = lead.polissa_id.titular.id

        mandate_id = mandate_o.search(
            self.cursor, self.uid, [("reference", "=", "res.partner,{}".format(titular_id))])[0]

        mandate = mandate_o.browse(self.cursor, self.uid, mandate_id)

        self.assertEqual(mandate.payment_type, "one_payment")

        invoice_id = account_invoice_o.search(
            self.cursor, self.uid, [("partner_id", "=", titular_id)])[0]

        invoice = account_invoice_o.browse(self.cursor, self.uid, invoice_id)

        self.assertFalse(invoice.sii_to_send)

        self.assertEqual(invoice.number, "QUOTA-SOCIA-LEAD-{}".format(lead.id))
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.state, "open")

        payment_mode_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "mode_pagament_socis_factura"
        )[1]

        payment_order = invoice.payment_order_id
        self.assertEqual(payment_order.state, 'draft')
        self.assertEqual(payment_order.mode.id, payment_mode_id)
        self.assertEqual(payment_order.total, -100)

        # Pay payment order
        payment_order_o.action_open(self.cursor, self.uid, [payment_order.id])
        with PatchNewCursors():
            context = {'active_ids': [payment_order.id], 'active_id': payment_order.id}
            wiz_pay_id = wiz_pay_o.create(
                self.cursor,
                self.uid,
                {'work_async': False},
                context=context,
            )
            wiz_pay_o.action_pagar_remesa_threaded(self.cursor.dbname, self.uid, [
                                                   wiz_pay_id], context=context)

        po = payment_order_o.browse(self.cursor, self.uid, payment_order.id)
        payment_line_ids = po.line_ids

        # Verify the payment lines after the payment
        for payment_line in payment_line_ids:
            self.assertEqual(payment_line.name, lead.member_number)
            self.assertEqual(payment_line.bank_id.iban, 'ES7712341234161234567890')
            self.assertEqual(payment_line.ml_inv_ref.state, 'paid')
            self.assertEqual(payment_line.order_id.reference, 'R{}/001'.format(datetime.now().year))
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_remesa_payment_but_not_new_member(self):
        www_lead_o = self.get_model("som.lead.www")
        account_invoice_o = self.get_model("account.invoice")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        mandate_o = self.get_model("payment.mandate")
        ir_model_o = self.get_model("ir.model.data")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        values["linked_member"] = "sponsored"
        values["contract_owner"] = values.pop("new_member_info")
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }
        values["payment_type"] = "remesa"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        titular_id = lead.polissa_id.titular.id

        mandate_id = mandate_o.search(
            self.cursor, self.uid, [("reference", "=", "res.partner,{}".format(titular_id))])

        # No mandate should be created for the titular
        self.assertEqual(len(mandate_id), 0)

        # No invoice should be created for the titular
        invoice_id = account_invoice_o.search(
            self.cursor, self.uid, [("partner_id", "=", titular_id)])
        self.assertEqual(len(invoice_id), 0)
