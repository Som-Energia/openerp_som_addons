# -*- encoding: utf-8 -*-
from ..component_utils import dateformat
from datetime import datetime


class TableReadings:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, invoice_ids, context={}):

        result = {}
        result["type"] = "TableReadings"
        result["taula"] = []
        result["distribuidora"] = "Sense F1 relacionat"
        result["date_from"] = False
        result["date_to"] = False
        fact_obj = wiz.pool.get("giscedata.facturacio.factura")
        f1_obj = wiz.pool.get("giscedata.facturacio.importacio.linia")

        for invoice_id in invoice_ids:
            linia_taula = {}
            invoice = fact_obj.browse(cursor, uid, invoice_id)
            if invoice.type in ("in_invoice", "in_refund"):
                search_params = [
                    ("cups_id.id", "=", invoice.cups_id.id),
                    ("invoice_number_text", "=", invoice.origin),
                ]
                f1_id = f1_obj.search(cursor, uid, search_params)
                if f1_id:
                    f1 = f1_obj.browse(cursor, uid, f1_id[0])
                else:
                    f1 = None
                if invoice.tipo_rectificadora in ("N", "G", "R", "A", "C") or (
                    f1.type_factura == "R"
                    if f1
                    else False
                    and invoice.ref.rectificative_type in ("N", "G")
                    and invoice.type == "in_invoice"
                ):  # F1 tipus R que rectifica una factura tipus N o G
                    if result["distribuidora"] == "Sense F1 relacionat":
                        result["distribuidora"] = (
                            f1.distribuidora_id.name if f1 else "Sense F1 relacionat"
                        )
                    linia_taula["invoice_number"] = invoice.origin
                    linia_taula["date"] = (
                        dateformat(f1.f1_date) if f1 else dateformat(invoice.date_invoice)
                    )
                    linia_taula["tipus_factura"] = (
                        "R" if invoice.tipo_rectificadora == "RA" else invoice.tipo_rectificadora
                    )
                    linia_taula["date_from"] = dateformat(
                        invoice.data_inici) if invoice.data_inici else linia_taula["date"]
                    if invoice.data_inici:
                        if not result["date_from"] or datetime.strptime(
                            invoice.data_inici, "%Y-%m-%d"
                        ) < datetime.strptime(result["date_from"], "%d-%m-%Y"):
                            result["date_from"] = dateformat(invoice.data_inici)
                    linia_taula["date_to"] = dateformat(invoice.data_final)
                    if invoice.data_final:
                        if not result["date_to"] or datetime.strptime(
                            invoice.data_final, "%Y-%m-%d"
                        ) > datetime.strptime(result["date_to"], "%d-%m-%Y"):
                            result["date_to"] = dateformat(invoice.data_final)

                    linia_taula["invoiced_energy"] = invoice.energia_kwh or 0
                    linia_taula["exported_energy"] = invoice.generacio_kwh or 0
                    linia_taula["invoiced_days"] = invoice.dies or 0
                    linia_taula["rectifying_invoice"] = (
                        invoice.rectifying_id.origin if invoice.rectifying_id else ""
                    )

                    result["taula"].append(linia_taula)
        result["taula"].sort(key=lambda x: (datetime.strptime(
            x['date_from'], "%d-%m-%Y"), x['tipus_factura']), reverse=True)

        return result
