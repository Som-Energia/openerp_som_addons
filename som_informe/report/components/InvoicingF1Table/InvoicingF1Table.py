from ..component_utils import dateformat

class InvoicingF1Table:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        fact_obj = wiz.pool.get('giscedata.facturacio.factura')
        search_parameters = [
            ('polissa_id', '=', wiz.polissa.id),
            ('type', 'in', ('in_invoice', 'in_refund')),
        ]
        if wiz.date_from:
            search_parameters.append(('data_inici', '>=', wiz.date_from))
        if wiz.date_to:
            search_parameters.append(('data_final', '<=', wiz.date_to))
        invoice_ids = fact_obj.search(cursor, uid, search_parameters)

        invoice_data = []
        for invoice_id in invoice_ids:
            invoice = fact_obj.browse(cursor, uid, invoice_id)
            data = {
                'invoice_number': invoice.origin,
                'invoice_type': invoice.rectificative_type,
                'invoice_date': dateformat(invoice.date_invoice),
                'date_from': dateformat(invoice.data_inici),
                'date_to': dateformat(invoice.data_final),
                'invoiced_days': invoice.dies,
                'invoiced_energy': invoice.energia_kwh,
                'amount_base': invoice.amount_untaxed,
                'amount_total': invoice.amount_total,
            }
            invoice_data.append(data)

        return {
            'type': 'InvoicingF1Table',
            'distri_name': wiz.polissa.distribuidora.name,
            'cups_name': wiz.polissa.cups.name,
            'invoices_f1_data': invoice_data,
            }