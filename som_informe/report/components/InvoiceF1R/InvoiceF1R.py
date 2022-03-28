from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude

class InvoiceF1R:
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

        result['numero_edm'] = f1.importacio_lectures_ids[0].comptador if f1.importacio_lectures_ids else ""

        #camps obligats per estructura
        result['type'] = 'InvoiceF1R'
        result['date'] = f1.f1_date if f1 else invoice.date_invoice

        result['distribuidora'] = f1.distribuidora_id.name
        result['invoice_type'] = invoice.rectificative_type
        result['invoice_date'] = dateformat(f1.f1_date) if f1 else dateformat(invoice.date_invoice)
        result['invoice_number'] = invoice.origin
        result['date_from'] = dateformat(invoice.data_inici)
        result['date_to'] = dateformat(invoice.data_final)
        result['rectifies_invoice'] = invoice.ref.origin #a testing F.Origen Rectificada/Anulada esta buit a totes :)

        result['linies'] = []
        if f1:
            for linia in f1.importacio_lectures_ids:
                dict_linia={}
                dict_linia['description_lectures'] = get_description(linia.origen_actual,"TABLA_44")
                #dict_linia['origen_lectures'] = linia.origen_actual
                #dict_linia['magnitud'] = linia.magnitud
                #dict_linia['periode'] = linia.periode
                dict_linia['magnitud_desc'] = get_description(linia.magnitud, "TABLA_43")
                dict_linia['periode_desc'] = get_description(linia.periode, "TABLA_42")
                dict_linia['lectura_inicial'] = linia.lectura_desde
                dict_linia['lectura_final'] = linia.lectura_actual
                dict_linia['consum_entre'] = linia.lectura_actual - linia.lectura_desde
                dict_linia['ajust'] = linia.ajust
                i_line = get_invoice_line(invoice, linia.magnitud, linia.periode)
                dict_linia['total_facturat'] = i_line.quantity if i_line else ""
                dict_linia['unit'] = get_unit_magnitude(linia.magnitud)

                result['linies'].append(dict_linia)


        return result