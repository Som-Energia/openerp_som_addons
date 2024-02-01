# -*- encoding: utf-8 -*-
from datetime import date
from ..component_utils import dateformat, get_description, get_invoice_line, get_unit_magnitude
from tools.translate import _

magnitud_description = {
    "AE": _("Energia activa entrant"),
    "AS": _("Energia activa sortint"),
    "EP": _("Excessos de potència"),
    "PM": _("Potència màxima"),
    "R1": _("Energia reactiva inductiva"),
    "R2": _("Energia reactiva en quadrant 2"),
    "R3": _("Energia reactiva en quadrant 3"),
    "R4": _("Energia reactiva capacitiva"),
}


def get_reading(invoice, date):
    reading = dateformat(date) + "Real"
    origin = "Real"
    return reading, origin


class InvoiceFE:
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

    def get_data(self, cursor, uid, wiz, invoice, context):
        # fact_obj = wiz.pool.get('giscedata.facturacio.factura')

        """start_reading, start_origin = get_reading(invoice, invoice.data_inici)
        end_reading, end_origin = get_reading(invoice, invoice.data_final)"""
        result = {}

        # camps obligats per estructura
        result["type"] = "InvoiceFE"
        result["date"] = invoice.date_invoice
        result["date_final"] = invoice.data_final
        if invoice.type == "out_invoice":
            result["tipo_factura"] = "Factura cliente"
        elif invoice.type == "out_refund":
            result["tipo_factura"] = "Factura rectificativa (abono) de cliente"
        result["invoice_date"] = (
            dateformat(invoice.origin_date_invoice)
            if invoice.origin_date_invoice
            else dateformat(invoice.date_invoice)
        )
        result["invoice_number"] = invoice.number
        result["numero_edm"] = (
            invoice.comptadors[0].name if invoice.comptadors else "Factura sense comptador associat"
        )
        result["invoiced_days"] = invoice.dies
        result["potencies"] = []
        for periode in invoice.polissa_id.potencies_periode:
            dict_potencies = {}
            dict_potencies["periode"] = periode.periode_id.name
            dict_potencies["potencia"] = periode.potencia
            result["potencies"].append(dict_potencies)
        result["amount_total"] = invoice.amount_total
        result["date_from"] = dateformat(invoice.data_inici)
        result["date_to"] = dateformat(invoice.data_final)
        result["other_concepts"] = []
        altres_lines = [
            l
            for l in invoice.linia_ids
            if l.tipus in ("altres", "cobrament")
            and l.invoice_line_id.product_id.code
            not in ("DN01", "BS01", "DESC1721", "DESC1721ENE", "DESC1721POT")
        ]
        for altra_linia in altres_lines:
            dict_altres = {}
            dict_altres["name"] = altra_linia.name
            dict_altres["price"] = altra_linia.price_subtotal
            result["other_concepts"].append(dict_altres)

        result["lectures"] = []
        for lectura in invoice.lectures_energia_ids:
            origens = self.get_origen_lectura(cursor, uid, lectura)
            dict_lectura = {}
            dict_lectura["magnitud_desc"] = magnitud_description[lectura.magnitud]
            dict_lectura["periode_desc"] = lectura.name[
                lectura.name.find("(") + 1 : lectura.name.find(")")
            ]
            dict_lectura["origen_lectura_inicial"] = lectura.origen_anterior_id.name
            dict_lectura["lectura_inicial"] = lectura.lect_anterior
            dict_lectura["origen_lectura_final"] = lectura.origen_id.name
            dict_lectura["lectura_final"] = lectura.lect_actual
            dict_lectura["consum_entre"] = (
                lectura.lect_actual - lectura.lect_anterior
            )  # lectura.consum
            # origen consum
            origin = "estimada"
            lectura_origen_anterior = origens[lectura.data_anterior]
            lectura_origen_actual = origens[lectura.data_actual]
            if lectura_origen_anterior == "real" and lectura_origen_actual == "real":
                origin = "real"
            elif (
                lectura_origen_anterior == "estimada distribuïdora"
                or lectura_origen_anterior == "real"
            ) and lectura_origen_actual == "calculada segons CCH":
                origin = "calculada"
            elif lectura_origen_anterior == "calculada segons CCH" and (
                lectura_origen_actual == "calculada segons CCH" or lectura_origen_actual == "real"
            ):
                origin = "calculada"
            dict_lectura["origen"] = origin

            dict_lectura["total_facturat"] = lectura.consum
            result["lectures"].append(dict_lectura)

        excess_lines = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0, "P6": 0}
        lines = [l for l in invoice.linia_ids if l.tipus == "exces_potencia"]
        result["maximetre"] = False
        if lines:
            result["maximetre"] = True
        for linia in lines:
            excess_lines[linia.name] = linia.quantity
        result["lectures_maximetre"] = []
        for lectura_maximetre in invoice.lectures_potencia_ids:
            lectures_m = {}
            lectures_m["periode"] = lectura_maximetre.name
            lectures_m["pot_contractada"] = lectura_maximetre.pot_contract
            lectures_m["pot_maximetre"] = lectura_maximetre.pot_maximetre
            lectures_m["exces"] = excess_lines[lectura_maximetre.name]
            result["lectures_maximetre"].append(lectures_m)

        return result
