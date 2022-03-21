from datetime import date
from ..component_utils import dateformat


def get_reading(invoice, date):
    reading = dateformat(date) + "Real"
    origin = "Real"
    return reading, origin

class InvoiceFE:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):
        #fact_obj = wiz.pool.get('giscedata.facturacio.factura')

        '''start_reading, start_origin = get_reading(invoice, invoice.data_inici)
        end_reading, end_origin = get_reading(invoice, invoice.data_final)'''
        result={}

        #camps obligats per estructura
        result['type'] = 'InvoiceFE'
        result['date'] = invoice.date_invoice

        # result['invoice_date'] = dateformat(invoice.date_invoice)
        # result['invoice_number'] = invoice.number
        # result['numero_edm'] = invoice.cups_id.comptador.polissa_comptador #error bool
        # result['invoiced_days'] = invoice.dies
        # result['amount_total'] = invoice.amount_total
        # result['date_from'] = dateformat(invoice.data_inici)
        # result['date_to'] = dateformat(invoice.data_final)
        #otros conceptos?

        return result


