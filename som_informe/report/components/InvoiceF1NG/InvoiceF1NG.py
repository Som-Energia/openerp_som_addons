from datetime import date
from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude

class InvoiceF1NG:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context={}):
        result = {}
        f1_obj = wiz.pool.get('giscedata.facturacio.importacio.linia')
        search_params = [
            ('cups_id.id', '=', invoice.cups_id.id),
            ('invoice_number_text', '=', invoice.origin),
        ]
        f1_id = f1_obj.search(cursor,uid,search_params)
        if f1_id:
            f1 = f1_obj.browse(cursor, uid, f1_id[0])
        else:
            f1 = None

        result['numero_edm'] = f1.importacio_lectures_ids[0].comptador if f1 and f1.importacio_lectures_ids else ""

        #camps obligats per estructura
        result['type'] = 'InvoiceF1NG'
        result['date'] = invoice.date_invoice

        result['distribuidora'] = f1.distribuidora_id.name if f1 else "Sense F1 relacionat"
        result['invoice_type'] = invoice.rectificative_type
        result['invoice_date'] = dateformat(invoice.date_invoice)
        result['invoice_number'] = invoice.origin
        result['date_from'] = dateformat(invoice.data_inici)
        result['date_to'] = dateformat(invoice.data_final)

        #taula

        result['linies'] = []
        if f1:
            for linia in f1.importacio_lectures_ids:
                dict_linia={}
                dict_linia['description_lectures'] = get_description(linia.origen_actual,"TABLA_44")
                dict_linia['origen_lectures'] = linia.origen_actual
                dict_linia['magnitud'] = linia.magnitud
                dict_linia['periode'] = linia.periode
                dict_linia['magnitud_desc'] = get_description(linia.magnitud, "TABLA_43")
                dict_linia['periode_desc'] = get_description(linia.periode, "TABLA_42")
                dict_linia['lectura_inicial'] = linia.lectura_desde
                dict_linia['lectura_final'] = linia.lectura_actual
                #el consum entre s'ha de calcular?
                dict_linia['consum_entre'] = linia.lectura_actual - linia.lectura_desde
                dict_linia['ajust'] = linia.ajust
                i_line = get_invoice_line(invoice, linia.magnitud, linia.periode)
                dict_linia['total_facturat'] = i_line.quantity if i_line else ""
                dict_linia['unit'] = get_unit_magnitude(linia.magnitud)

                result['linies'].append(dict_linia)


        result['invoiced_days'] = invoice.dies
        result['invoiced_energy'] = invoice.energia_kwh
        result['amount_base'] = invoice.amount_untaxed
        result['amount_total'] = invoice.amount_total

        '''
        fact_ob = fact.search([('type','=','in_invoice')],limit=1) id 13803452
        fact_3 = fact.browse(fact_ob[0])
        f1_obj = O_testing.model('giscedata.facturacio.importacio.linia')
        id3 = f1_obj.search([('invoice_number_text','=',fact_3.origin)] id 8228697
        f1_obj.browse(id3).importacio_lectures_ids[0].read()
        f1_obj.browse(id3).importacio_lectures_ids[0][0].comptador
        '''


        return result

