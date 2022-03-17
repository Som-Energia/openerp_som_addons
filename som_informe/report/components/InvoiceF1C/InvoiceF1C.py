from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude
from .. .. ..erp.addons.gisce.GISCEMaster.giscedata_facturacio.defs import TIPO_FACTURA_SELECTION

class InvoiceF1C:
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
        result['type'] = 'InvoiceF1C'
        result['date'] = invoice.date_invoice

        result['distribuidora'] = f1.distribuidora_id.name
        result['invoice_type'] = invoice.rectificative_type
        result['invoice_date'] = dateformat(invoice.date_invoice)
        result['invoice_number'] = invoice.origin
        result['date_from'] = dateformat(invoice.data_inici)
        result['date_to'] = dateformat(invoice.data_final)

        result['concept'] = dict(TIPO_FACTURA_SELECTION).get(invoice.tipo_factura, "")
        result['complement_invoice'] = invoice.ref.origin
        result['num_expedient'] = f1_obj.num_expedient
        result['comentaris'] =f1_obj.comentari

        #taula
        #F1 tipus C no tenen lectures per tant
        #taula de linies de factura en comptes de lectures?

        return result