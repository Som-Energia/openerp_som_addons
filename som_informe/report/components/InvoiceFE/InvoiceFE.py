# -*- encoding: utf-8 -*-
from datetime import date
from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude, get_origen_lectura


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
        result['date_final'] = invoice.data_final
        if invoice.type == 'out_invoice':
            result['tipo_factura'] = 'Factura cliente'
        elif invoice.type == 'out_refund':
            result['tipo_factura'] = 'Factura rectificativa (abono) de cliente'
        result['invoice_date'] = dateformat(invoice.date_invoice)
        result['invoice_number'] = invoice.number
        result['numero_edm'] = invoice.comptador[0].name if invoice.comptador else "Factura sense comptador associat"
        result['invoiced_days'] = invoice.dies
        result['potencies'] = []
        for periode in invoice.polissa_id.potencies_periode:
            dict_potencies={}
            dict_potencies['periode'] = periode.periode_id.name
            dict_potencies['potencia'] = periode.potencia
            result['potencies'].append(dict_potencies)
        result['amount_total'] = invoice.amount_total
        result['date_from'] = dateformat(invoice.data_inici)
        result['date_to'] = dateformat(invoice.data_final)
        result['other_concepts'] = []
        altres_lines = [l for l in invoice.linia_ids if l.tipus in ('altres', 'cobrament')
                            and l.invoice_line_id.product_id.code not in  ('DN01', 'BS01', 'DESC1721', 'DESC1721ENE', 'DESC1721POT')
        ]
        for altra_linia in altres_lines:
            dict_altres = {}
            dict_altres['name'] = altra_linia.name
            dict_altres['price'] = altra_linia.price_subtotal
            result['other_concepts'].append(dict_altres)

        result['lectures'] = {}
        for lectura in invoice.lectures_energia_ids:
            origens = get_origen_lectura(lectura)
            dict_lectura = {}
            dict_lectura['magnitud_desc'] = get_description(lectura.magnitud, "TABLA_43")
            dict_lectura['periode_desc'] = get_description(lectura.periode, "TABLA_42")
            dict_lectura['origen_lectura_inicial'] = lectura.origen_anterior_id.name
            dict_lectura['lectura_inicial'] = lectura.lect_anterior
            dict_lectura['origen_lectura_final'] = lectura.origen_id.name
            dict_lectura['lectura_final'] = lectura.lect_actual
            dict_lectura['consum_entre'] = lectura.lect_actual-lectura.lect_anterior #lect.consum
            #origen consum
            origin = 'estimada'
            lectura_origen_anterior = origens(lectura.data_anterior)
            lectura_origen_actual = origens(lectura.data_actual)
            if lectura_origen_anterior == 'real' and lectura_origen_actual =='real':
                origin = 'real'
            elif (lectura_origen_anterior == 'estimada distribuïdora' or lectura_origen_anterior == 'real') and lectura_origen_actual == 'calculada segons CCH':
                origin = 'calculada'
            elif lectura_origen_anterior == 'calculada segons CCH' and (lectura_origen_actual =='calculada segons CCH' or lectura_origen_actual == 'real'):
                origin = 'calculada'
            dict_lectura['origen'] = origin

            dict_lectura['total_facturat'] = 0.0 # esperant aclariment de ET (KWh o EUR ?)
            result['lectures'].append(dict_lectura)

        return result


