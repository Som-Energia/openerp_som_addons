# -*- coding: utf-8 -*-
from osv import osv, fields
import netsvc
import traceback
import base64


class WizardReprintInvoiceSom(osv.osv_memory):
    _name = "wizard.reprint.invoice.som"

    def reprint_pdf(self, cursor, uid, ids, context=None):  # noqa: C901
        if context is None:
            context = {}

        f_id = ids[0]
        ok, pdf = self._generate_pdf(cursor, uid, f_id, context=context)
        if ok:
            return (base64.encodestring(pdf), u'pdf')

    def reprint_and_store(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

    def _generate_pdf(self, cursor, uid, res_id, context=None):
        report_name = 'report.giscedata.facturacio.factura'
        res_ids = [res_id]
        values = {
            "model": "giscedata.facturacio.comer.som",
            "id": res_ids,
            "report_type": "pdf",
        }
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['force_store_pdf_disabled'] = True
        try:
            report = netsvc.service_exist(report_name)
            result = report.create(cursor, uid, res_ids, values, ctx)
            return True, result[0]
        except Exception:
            tb = traceback.format_exc()
            return False, tb

    _columns = {
        "info": fields.text("Description"),
    }

    _defaults = {
    }


WizardReprintInvoiceSom()
