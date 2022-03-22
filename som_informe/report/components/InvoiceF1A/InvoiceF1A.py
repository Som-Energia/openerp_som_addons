from ..component_utils import dateformat

class InvoiceF1A:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):

        result = {}
        f1_obj = wiz.pool.get('giscedata.facturacio.importacio.linia')
        search_params = [
            ('cups_id.id', '=', invoice.cups_id.id),
            ('invoice_number_text', '=', invoice.origin),
        ]
        f1_id = f1_obj.search(cursor,uid,search_params)
        f1 = f1_obj.browse(cursor, uid, f1_id[0])

        #camps obligats per estructura
        result['type'] = 'InvoiceF1A'
        result['date'] = f1.f1_date if f1 else invoice.date_invoice
        result['date_to'] = dateformat(invoice.data_final) #conservem pel futur possible desempat

        result['distribuidora'] = f1.distribuidora_id.name
        result['invoice_type'] = invoice.rectificative_type
        result['invoice_date'] = dateformat(f1.f1_date) if f1 else dateformat(invoice.date_invoice)
        result['invoice_number'] = invoice.origin
        result['cancel_invoice'] = invoice.ref.origin #a testing F.Origen Rectificada/Anulada esta buit a totes :)

        return result