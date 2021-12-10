from datetime import date
from ..component_utils import dateformat


def get_reading(invoice, date):
    reading = dateformat(date) + "Real"
    origin = "Real"
    return reading, origin

class InvoiceFE:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, invoice, context):
        #fact_obj = wiz.pool.get('giscedata.facturacio.factura')
        '''search_parameters = [
            ('polissa_id', '=', wiz.polissa.id),
            ('type', 'in', ('out_invoice', 'out_refund')),
        ]
        if wiz.date_from:
            search_parameters.append(('data_inici', '>=', wiz.date_from))
        if wiz.date_to:
            search_parameters.append(('data_final', '<=', wiz.date_to))
        invoice_ids = fact_obj.search(cursor, uid, search_parameters)

        invoice_data = []
        for invoice_id in invoice_ids:'''
        #invoice = fact_obj.browse(cursor, uid, invoice_id)

        '''start_reading, start_origin = get_reading(invoice, invoice.data_inici)
        end_reading, end_origin = get_reading(invoice, invoice.data_final)'''
        result={}
        result['invoice_number'] = invoice.origin
        result['amount_base'] = invoice.amount_untaxed
        result['amount_total'] = invoice.amount_total
        result['invoice_date'] = dateformat(invoice.date_invoice)
        result['date'] = invoice.date_invoice
        result['due_date'] = dateformat(invoice.due_invoice)
        result['invoiced_days'] = invoice.dies
        result['invoiced_energy'] = invoice.energia_kwh
        result['invoiced_power'] = invoice.potencia
        result['readings_origin'] = "Invent"
        return result


