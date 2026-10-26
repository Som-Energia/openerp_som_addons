# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv


class SomL10nEsAeatMod347CalculateRecords(osv.osv_memory):
    _name = "l10n.es.aeat.mod347.calculate_records"
    _inherit = "l10n.es.aeat.mod347.calculate_records"

    def _get_mod347_amount_exclusions(
        self,
        cr,
        uid,
        partner_ids,
        invoice_type,
        period_ids,
        sii_send_invoices=False,
        context=None,
    ):
        if context is None:
            context = {}

        exclusions = super(
            SomL10nEsAeatMod347CalculateRecords, self
        )._get_mod347_amount_exclusions(
            cr,
            uid,
            partner_ids,
            invoice_type,
            period_ids,
            sii_send_invoices=sii_send_invoices,
            context=context,
        )

        account_obj = self.pool.get("account.account")
        donation_account_ids = account_obj.search(
            cr, uid, [("name", "=", "DONATIUS")], context=context
        )
        if not donation_account_ids:
            return exclusions

        invoice_domain = [
            ("partner_id", "in", partner_ids),
            ("type", "=", invoice_type),
            ("period_id", "in", period_ids),
            ("state", "in", ["open", "paid"]),
            ("move_id", "!=", None),
        ]
        if sii_send_invoices:
            invoice_domain.append(("sii_registered", "=", True))

        invoice_obj = self.pool.get("account.invoice")
        invoice_ids = invoice_obj.search(
            cr, uid, invoice_domain, context=context
        )
        if not invoice_ids:
            return exclusions

        invoice_by_id = dict(
            (invoice.id, invoice)
            for invoice in invoice_obj.browse(cr, uid, invoice_ids)
        )
        invoice_line_obj = self.pool.get("account.invoice.line")
        invoice_line_ids = invoice_line_obj.search(
            cr,
            uid,
            [
                ("invoice_id", "in", invoice_ids),
                ("account_id", "in", donation_account_ids),
            ],
            context=context,
        )
        for line in invoice_line_obj.read(
            cr, uid, invoice_line_ids, ["invoice_id", "price_subtotal"],
            context=context,
        ):
            invoice_relation = line.get("invoice_id")
            if not invoice_relation:
                continue
            invoice_id = invoice_relation[0]
            invoice = invoice_by_id.get(invoice_id)
            if not invoice:
                continue

            amount = line.get("price_subtotal") or 0.0
            quarter = invoice.period_id.quarter
            exclusions["total"] += amount
            exclusions["quarters"][quarter] = (
                exclusions["quarters"].get(quarter, 0.0) + amount
            )
            exclusions["invoices"][invoice_id] = (
                exclusions["invoices"].get(invoice_id, 0.0) + amount
            )

        return exclusions


SomL10nEsAeatMod347CalculateRecords()
