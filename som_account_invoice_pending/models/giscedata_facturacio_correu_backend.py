# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify


class ReportBackendInvoiceEmail(ReportBackend):
    _name = "report.backend.invoice.email"
    _inherit = "report.backend.invoice.email"

    @report_browsify
    def get_factura(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        data = super(ReportBackendInvoiceEmail, self).get_factura(cursor, uid, fra, context=context)

        polissa_o = self.pool.get("giscedata.polissa")
        ctxt = {"date": fra.data_final.val}
        pol = polissa_o.browse(cursor, uid, fra.polissa_id.id, context=ctxt)

        if pol.cobrament_bloquejat and fra.pending_state:
            ir_model_data = self.pool.get("ir.model.data")
            fue_bs = ir_model_data.get_object_reference(
                cursor, uid,
                "som_account_invoice_pending",
                "fue_bo_social_pending_state"
            )[1]

            fue_df = ir_model_data.get_object_reference(
                cursor, uid,
                "som_account_invoice_pending",
                "fue_default_pending_state"
            )[1]

            r1_bs = ir_model_data.get_object_reference(
                cursor, uid,
                "som_account_invoice_pending",
                "reclamacio_en_curs_pending_state"
            )[1]

            r1_df = ir_model_data.get_object_reference(
                cursor, uid,
                "som_account_invoice_pending",
                "default_reclamacio_en_curs_pending_state"
            )[1]
            blocked_payment_states = [fue_bs, fue_df, r1_bs, r1_df]
            data["hasBlockedPayment"] = fra.pending_state.id in blocked_payment_states
        else:
            data["hasBlockedPayment"] = False

        return data


ReportBackendInvoiceEmail()
