from datetime import date
from ..component_utils import dateformat
class InvoiceF1NG:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):
        result = {}
        import pudb; pu.db
        f1_obj = wiz.pool.get('giscedata.facturacio.importacio.linia')
        search_params = [
            ('invoice_number_text', '=', invoice.origin),
        ]
        f1_id = f1_obj.search(cursor,uid,search_params)
        f1 = f1_obj.browse(cursor, uid, f1_id[0])
        #for linia in f1.importacio_lectures_ids:
        result['numero_edm'] = f1.importacio_lectures_ids[0][0].comptador

        result['type'] = 'InvoiceF1NG'
        result['date'] = invoice.date_invoice
        result['invoice_number'] = invoice.origin
        result['invoice_type'] = invoice.rectificative_type
        result['invoice_date'] = dateformat(invoice.date_invoice)
        result['date_from'] = dateformat(invoice.data_inici)
        result['date_to'] = dateformat(invoice.data_final)
        result['invoiced_days'] = invoice.dies
        result['invoiced_energy'] = invoice.energia_kwh
        result['amount_base'] = invoice.amount_untaxed
        result['amount_total'] = invoice.amount_total

        '''
        fact_ob = fact.search([('type','=','in_invoice')],limit=1) id 13803452
        fact_3 = fact.browse(fact_ob[0])
        f1_obj = O_testing.model('giscedata.facturacio.importacio.linia')
        id3 = f1_obj.search([('invoice_number_text','=',fact_3.origin)]
        f1_obj.browse(id3).importacio_lectures_ids[0].read()
        f1_obj.browse(id3).importacio_lectures_ids[0][0].comptador

        '''


        return result

