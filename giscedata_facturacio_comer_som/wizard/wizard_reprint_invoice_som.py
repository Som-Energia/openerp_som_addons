# -*- coding: utf-8 -*-
from osv import osv, fields
import netsvc
import traceback
from ..invoice_pdf_storer import InvoicePdfStorer


class WizardReprintInvoiceSom(osv.osv_memory):
    _name = "wizard.reprint.invoice.som"

    def reprint_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        fact_ids = context.get('active_ids', None)
        if not fact_ids:
            res_id = context.get('active_id', None)
            if res_id:
                fact_ids = [res_id]
            else:
                fact_ids = []

        ctx = context.copy()
        ctx['force_store_pdf_disabled'] = True

        return {
            'type': 'ir.actions.report.xml',
            'model': 'giscedata.facturacio.factura',
            'report_name': 'giscedata.facturacio.factura',
            'datas': {
                'ids': fact_ids,
            },
            'context': ctx
        }

    def reprint_and_store(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        fact_ids = context.get('active_ids', None)
        if not fact_ids:
            res_id = context.get('active_id', None)
            if res_id:
                fact_ids = [res_id]
            else:
                fact_ids = []

        msg = u''
        storer = InvoicePdfStorer(cursor, uid, context)
        for fact_id in fact_ids:
            result = self._generate_pdf(cursor, uid, fact_id, context=context)
            fact_number = storer.get_storable_fact_number(fact_id)
            if fact_number and result[0]:
                file_name = storer.get_store_filename(fact_number)
                stored_ids = storer.exists_file(file_name, fact_id)
                storer.mark_as_old_file(stored_ids)
                storer.store_file(result[1], file_name, fact_id)
                msg += u'Factura {} generada i guardada com adjunt de id: {}\n\n'.format(
                    fact_number, fact_id
                )
            if not fact_number:
                msg += u'Factura amb id {} no té numero\n'.format(
                    fact_id
                )
            if not result[0]:
                msg += u'Factura amb id {} i numero {} te errors en generar:\n'.format(
                    fact_id, fact_number
                )
                msg += result[1]
                msg += '\n\n'

        self.write(cursor, uid, ids, {"state": "end", "info": msg})

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
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text("Informació", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: "",
    }


WizardReprintInvoiceSom()
