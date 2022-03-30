# -*- encoding: utf-8 -*-
from datetime import date
from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude

class InvoiceF1NG:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context={}):

        #giscedata_facturacio.defs.TIPO_FACTURA_SELECTION
        TIPO_FACTURA_SELECTION = [('01', 'Normal'),
                          ('02', 'Modificación de Contrato'),
                          ('03', 'Baja de Contrato'),
                          ('04', 'Derechos de Contratacion'),
                          ('05', 'Deposito de garantía'),
                          ('06', 'Inspección - Anomalia'),
                          ('07', 'Atenciones (verificaciones, )'),
                          ('08', 'Indemnizacion'),
                          ('09', 'Intereses de demora'),
                          ('10', 'Servicios'),
                          ('11', 'Inspección - Fraude')]

        result = {}
        f1_obj = wiz.pool.get('giscedata.facturacio.importacio.linia')
        facturacio_imp_linia_obj= wiz.pool.get('giscedata.facturacio.importacio.linia.factura')

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
        result['date'] = f1.f1_date if f1 else invoice.date_invoice

        result['distribuidora'] = f1.distribuidora_id.name if f1 else "Sense F1 relacionat"
        result['invoice_type'] = invoice.rectificative_type
        result['invoice_date'] = dateformat(f1.f1_date) if f1 else dateformat(invoice.date_invoice)
        result['invoice_number'] = invoice.origin
        result['date_from'] = dateformat(invoice.data_inici)
        result['date_to'] = dateformat(invoice.data_final)
        result['type_f1'] = f1.tipo_factura_f1
        result['concept'] = dict(TIPO_FACTURA_SELECTION).get(invoice.tipo_factura, "")

        #taula
        result['linies'] = []
        result['linies_extra'] = []
        if f1:
            if f1.tipo_factura_f1 == 'atr':
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
            elif f1.tipo_factura_f1 == 'otros':
                for linia_extra in f1.liniaextra_id:
                    dict_linia={}
                    dict_linia['name'] = linia_extra.name
                    dict_linia['total'] = linia_extra.price_subtotal
                    result['linies_extra'].append(dict_linia)

        #estaven aqui però no al mako
        # result['invoiced_days'] = invoice.dies
        # result['invoiced_energy'] = invoice.energia_kwh
        # result['amount_base'] = invoice.amount_untaxed
        # result['amount_total'] = invoice.amount_total

        return result

