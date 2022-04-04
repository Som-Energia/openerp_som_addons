# -*- encoding: utf-8 -*-
from ..component_utils import dateformat

class TableReadings:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice_ids, context={}):

        result = []
        f1_obj = wiz.pool.get('giscedata.facturacio.importacio.linia')

        for invoice in invoice_ids:
            linia_taula = {}
            search_params = [
                ('cups_id.id', '=', invoice.cups_id.id),
                ('invoice_number_text', '=', invoice.origin),
            ]
            f1_id = f1_obj.search(cursor,uid,search_params)
            if f1_id:
                f1 = f1_obj.browse(cursor, uid, f1_id[0])
            else:
                f1 = None
            linia_taula['invoice_number'] = invoice.number
            linia_taula['invoice_code'] = invoice.origin
            linia_taula['date_from'] = dateformat(invoice.data_inici)
            linia_taula['date_to'] = dateformat(invoice.data_final)
            linia_taula['date'] = dateformat(f1.f1_date) if f1 else invoice.date_invoice
            linia_taula['invoiced_energy'] = invoice.energia_kwh
            linia_taula['exported_energy'] = invoice.generacio_kwh or 0
            linia_taula['invoiced_days'] = invoice.dies

            result.append(linia_taula)

        return result
