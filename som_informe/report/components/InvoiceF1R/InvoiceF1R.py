from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude


class InvoiceF1R:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice, context):

        result = {}
        f1_obj = wiz.pool.get("giscedata.facturacio.importacio.linia")
        search_params = [
            ("cups_id.id", "=", invoice.cups_id.id),
            ("invoice_number_text", "=", invoice.origin),
        ]
        f1_id = f1_obj.search(cursor, uid, search_params)
        f1 = f1_obj.browse(cursor, uid, f1_id[0])

        result["numero_edm"] = (
            f1.importacio_lectures_ids[0].comptador if f1.importacio_lectures_ids else ""
        )

        # camps obligats per estructura
        result["type"] = "InvoiceF1R"
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
        result["date_from"] = (
            dateformat(invoice.data_inici)
            if invoice.data_inici
            else dateformat(invoice.date_invoice)
        )
        result["date_to"] = (
            dateformat(invoice.data_final)
            if invoice.data_final
            else dateformat(invoice.date_invoice)
        )
        result[
            "rectifies_invoice"
        ] = invoice.ref.origin  # a testing F.Origen Rectificada/Anulada esta buit a totes :)

        result["linies"] = []
        if f1:
            for linia in f1.importacio_lectures_ids:
                dict_linia = {}
                dict_linia["origen_lectura_final"] = get_description(
                    linia.origen_actual, "TABLA_44"
                )
                dict_linia["origen_lectura_inicial"] = get_description(
                    linia.origen_desde, "TABLA_44"
                )
                dict_linia["magnitud_desc"] = get_description(linia.magnitud, "TABLA_43")
                dict_linia["periode_desc"] = get_description(linia.periode, "TABLA_42")
                dict_linia["lectura_inicial"] = linia.lectura_desde
                dict_linia["lectura_final"] = linia.lectura_actual
                dict_linia["consum_entre"] = linia.lectura_actual - linia.lectura_desde
                dict_linia["ajust"] = linia.ajust
                i_line = get_invoice_line(invoice, linia.magnitud, linia.periode)
                dict_linia["total_facturat"] = i_line.quantity if i_line else ""
                dict_linia["unit"] = get_unit_magnitude(linia.magnitud)

                result["linies"].append(dict_linia)

        return result
