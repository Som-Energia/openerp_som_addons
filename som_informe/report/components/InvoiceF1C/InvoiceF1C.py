# -*- encoding: utf-8 -*-
from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude

# from .. .. ..erp.addons.gisce.GISCEMaster.giscedata_facturacio.defs import TIPO_FACTURA_SELECTION


class InvoiceF1C:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):
        # giscedata_facturacio.defs.TIPO_FACTURA_SELECTION
        TIPO_FACTURA_SELECTION = [
            ("01", "Normal"),
            ("02", "Modificación de Contrato"),
            ("03", "Baja de Contrato"),
            ("04", "Derechos de Contratacion"),
            ("05", "Deposito de garantía"),
            ("06", "Inspección - Anomalia"),
            ("07", "Atenciones (verificaciones, )"),
            ("08", "Indemnizacion"),
            ("09", "Intereses de demora"),
            ("10", "Servicios"),
            ("11", "Inspección - Fraude"),
        ]

        result = {}
        f1_obj = wiz.pool.get("giscedata.facturacio.importacio.linia")
        search_params = [
            ("cups_id.id", "=", invoice.cups_id.id),
            ("invoice_number_text", "=", invoice.origin),
        ]
        f1_id = f1_obj.search(cursor, uid, search_params)
        f1 = f1_obj.browse(cursor, uid, f1_id[0])

        # camps obligats per estructura
        result["type"] = "InvoiceF1C"
        result["date"] = (f1.f1_date if f1 else invoice.date_invoice)[:10]
        result["date_final"] = f1.fecha_factura_hasta if f1 else invoice.data_final

        result["distribuidora"] = f1.distribuidora_id.name
        result["invoice_type"] = invoice.rectificative_type
        result["invoice_date"] = (
            dateformat(invoice.origin_date_invoice)
            if invoice.origin_date_invoice
            else dateformat(invoice.date_invoice)
        )
        result["invoice_number"] = invoice.origin
        result["date_from"] = dateformat(invoice.data_inici)
        result["date_to"] = dateformat(invoice.data_final)

        result["concept"] = dict(TIPO_FACTURA_SELECTION).get(invoice.tipo_factura, "")

        result["num_expedient"] = f1.num_expedient
        result["comentaris"] = f1.comentari

        # taula
        result["linies"] = []
        for linia in invoice.linia_ids:
            dict_linia = {}
            if "Total" in linia.name:
                continue
            dict_linia["name"] = linia.name
            dict_linia["tipus"] = linia.tipus
            dict_linia["quantity"] = linia.quantity
            dict_linia["uom"] = linia.uos_id.name

            result["linies"].append(dict_linia)

        return result
