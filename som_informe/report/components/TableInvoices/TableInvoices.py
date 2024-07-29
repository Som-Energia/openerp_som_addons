# -*- encoding: utf-8 -*-
from ..component_utils import dateformat
from datetime import datetime, timedelta


class TableInvoices:
    def __init__(self):
        pass

    def get_origen_lectura(self, cursor, uid, lectura):
        """Busquem l'origen de la lectura cercant-la a les lectures de facturació"""
        res = {lectura.data_actual: "", lectura.data_anterior: ""}

        lectura_obj = lectura.pool.get("giscedata.lectures.lectura")
        tarifa_obj = lectura.pool.get("giscedata.polissa.tarifa")
        origen_obj = lectura.pool.get("giscedata.lectures.origen")
        origen_comer_obj = lectura.pool.get("giscedata.lectures.origen_comer")

        estimada_id = origen_obj.search(cursor, uid, [("codi", "=", "40")])[0]
        sin_lectura_id = origen_obj.search(cursor, uid, [("codi", "=", "99")])[0]
        estimada_som_id = origen_comer_obj.search(cursor, uid, [("codi", "=", "ES")])[0]
        calculada_som_id = origen_obj.search(cursor, uid, [("codi", "=", "LC")])
        calculada_som_id = calculada_som_id[0] if calculada_som_id else None

        # Busquem la tarifa
        tarifa_id = tarifa_obj.search(cursor, uid, [("name", "=", lectura.name[:-5])])
        if tarifa_id:
            tipus = lectura.tipus == "activa" and "A" or "R"

            search_vals = [
                ("comptador", "=", lectura.comptador),
                ("periode.name", "=", lectura.name[-3:-1]),
                ("periode.tarifa", "=", tarifa_id[0]),
                ("tipus", "=", tipus),
                ("name", "in", [lectura.data_actual, lectura.data_anterior]),
            ]
            lect_ids = lectura_obj.search(cursor, uid, search_vals)
            lect_vals = lectura_obj.read(
                cursor, uid, lect_ids, ["name", "origen_comer_id", "origen_id"]
            )
            for lect in lect_vals:
                # En funció dels origens, escrivim el text
                # Si Estimada (40) o Sin Lectura (99) i Estimada (ES): Estimada Somenergia
                # Si Estimada (40) o Sin Lectura (99) i F1/Q1/etc...(!ES): Estimada distribuïdora
                # La resta: Real
                origen_txt = "real"
                if lect["origen_id"][0] in [estimada_id, sin_lectura_id]:
                    if lect["origen_comer_id"][0] == estimada_som_id:
                        origen_txt = "calculada per Som Energia"
                    else:
                        origen_txt = "estimada distribuïdora"
                if lect["origen_id"][0] == calculada_som_id:
                    origen_txt = "calculada segons CCH"
                res[lect["name"]] = "%s" % (origen_txt)

        return res

    def get_data(self, cursor, uid, wiz, invoice_ids, context={}):
        result = {}
        result["type"] = "TableInvoices"
        result["taula"] = []
        result["date_from"] = False
        result["date_to"] = False
        fact_obj = wiz.pool.get("giscedata.facturacio.factura")
        for invoice_id in invoice_ids:
            invoice = fact_obj.browse(cursor, uid, invoice_id)
            if invoice.type in ("out_invoice", "out_refund") and invoice.state in ("paid", "open"):
                linia_taula = {}
                linia_taula["invoice_number"] = invoice.number
                linia_taula["date"] = dateformat(invoice.date_invoice)
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
                linia_taula["max_power"] = invoice.potencia_max or 0
                linia_taula["invoiced_energy"] = invoice.energia_kwh or 0
                linia_taula["exported_energy"] = invoice.generacio_kwh or 0
                linia_taula["origin"] = self.get_invoice_origin(cursor, uid, invoice)
                linia_taula["invoiced_days"] = invoice.dies or 0
                linia_taula["total"] = invoice.signed_amount_total
                result["taula"].append(linia_taula)
        result["taula"].sort(key=lambda x: datetime.strptime(
            x['date_from'], "%d-%m-%Y"))
        return result

    def get_invoice_origin(self, cursor, uid, invoice):
        readings = {}
        lectures = invoice.lectures_energia_ids
        if lectures != None:  # noqa: E711
            for lectura in lectures:
                origens = self.get_origen_lectura(cursor, uid, lectura)
                if "(P1)" in lectura.name:
                    data = str(
                        datetime.strptime(lectura.data_anterior, "%Y-%m-%d").date()
                        + timedelta(days=1)
                    )
                    origin = u"estimada"
                    if (
                        origens[lectura.data_anterior] == "real"
                        and origens[lectura.data_actual] == "real"
                    ):
                        origin = u"real"
                    elif (
                        origens[lectura.data_anterior] == "estimada distribuïdora"
                        or origens[lectura.data_anterior] == "real"
                    ) and origens[lectura.data_actual] == "calculada segons CCH":
                        origin = u"calculada"
                    elif origens[lectura.data_anterior] == "calculada segons CCH" and (
                        origens[lectura.data_actual] == "calculada segons CCH"
                        or origens[lectura.data_actual] == "real"
                    ):
                        origin = u"calculada"

                    readings[data] = origin

            return (
                readings[invoice.data_inici]
                if invoice.data_inici in readings
                else (u"sense lectura")
            )
