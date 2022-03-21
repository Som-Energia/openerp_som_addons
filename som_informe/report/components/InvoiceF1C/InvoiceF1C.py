# -*- encoding: utf-8 -*-
from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude
#from .. .. ..erp.addons.gisce.GISCEMaster.giscedata_facturacio.defs import TIPO_FACTURA_SELECTION

class InvoiceF1C:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):
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
        search_params = [
            ('cups_id.id', '=', invoice.cups_id.id),
            ('invoice_number_text', '=', invoice.origin),
        ]
        f1_id = f1_obj.search(cursor,uid,search_params)
        f1 = f1_obj.browse(cursor, uid, f1_id[0])

        #camps obligats per estructura
        result['type'] = 'InvoiceF1C'
        result['date'] = f1.f1_date

        result['distribuidora'] = f1.distribuidora_id.name
        result['invoice_type'] = invoice.rectificative_type
        result['invoice_date'] = dateformat(f1.f1_date)
        result['invoice_number'] = invoice.origin
        result['date_from'] = dateformat(invoice.data_inici)
        result['date_to'] = dateformat(invoice.data_final)

        result['concept'] = dict(TIPO_FACTURA_SELECTION).get(invoice.tipo_factura, "")
        if f1_obj.num_expedient:
            result['num_expedient'] = f1_obj.num_expedient
        if f1_obj.comentari:
            result['comentaris'] =f1_obj.comentari

        #taula
        result['linies'] = []
        for linia in invoice.linia_ids:
            dict_linia={}
            dict_linia['name'] = linia.name
            dict_linia['tipus'] = linia.tipus
            dict_linia['quantity'] = linia.quantity
            dict_linia['uom'] = linia.uos_id.name
            dict_linia['price'] = linia.price_unit_multi
            dict_linia['extra_op'] = linia.multi
            dict_linia['discount'] = linia.discount
            dict_linia['subtotal'] = linia.price_subtotal

            result['linies'].append(dict_linia)

        return result