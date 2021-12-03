from ..component_utils import dateformat

def get_reading(invoice, date):
    reading = dateformat(date) + "Real"
    origin = "Real"
    return reading, origin

class InvoicingFeTable:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        fact_obj = wiz.pool.get('giscedata.facturacio.factura')
        search_parameters = [
            ('polissa_id', '=', wiz.polissa.id),
            ('type', 'in', ('out_invoice', 'out_refund')),
        ]
        if wiz.date_from:
            search_parameters.append(('data_inici', '>=', wiz.date_from))
        if wiz.date_to:
            search_parameters.append(('data_final', '<=', wiz.date_to))
        invoice_ids = fact_obj.search(cursor, uid, search_parameters)

        invoice_data = []
        for invoice_id in invoice_ids:
            invoice = fact_obj.browse(cursor, uid, invoice_id)

            start_reading, start_origin = get_reading(invoice, invoice.data_inici)
            end_reading, end_origin = get_reading(invoice, invoice.data_final)

            data = {
                'invoice_number': invoice.origin,
                'amount_base': invoice.amount_untaxed,
                'amount_total': invoice.amount_total,
                'invoice_date': dateformat(invoice.date_invoice),
                'due_date': dateformat(invoice.due_invoice),
                'invoiced_days': invoice.dies,
                'invoiced_energy': invoice.energia_kwh,
                'invoiced_power': invoice.potencia,
                'date_from_plus_readings': start_reading,
                'date_to_plus_readings': end_reading,
                'readings_origin': "Invent",
            }
            invoice_data.append(data)

        return {
            'type': 'InvoicingFeTable',
            'cups_name': wiz.polissa.cups.name,
            'invoices_fe_data': invoice_data,
            }

