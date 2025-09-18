# -*- coding: utf-8 -*-
from osv import osv, fields
import netsvc
import traceback


class WizardReprintInvoiceSom(osv.osv_memory):
    _name = "wizard.reprint.invoice.som"

    def reprint_pdf(self, cursor, uid, ids, context=None):  # noqa: C901
        if context is None:
            context = {}

        res_ids = context.get('active_ids', None)
        if res_ids:
            res_id = res_ids[0]
        else:
            res_id = context.get('active_id', None)

        ctx = context.copy()
        ctx['force_store_pdf_disabled'] = True

        return {
            'type': 'ir.actions.report.xml',
            'model': 'giscedata.facturacio.factura',
            'report_name': 'giscedata.facturacio.factura',
            'datas': {
                'ids': [res_id],
                'context': ctx,
            }
        }

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
