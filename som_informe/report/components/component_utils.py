# -*- encoding: utf-8 -*-
from gestionatr.utils import get_description as gestion_atr_get_description
from datetime import datetime

magnitud_a_tipus = {
    "AE": "energia",
    "AS": "generacio",
    "PM": "potencia",
    "EP": "exces_potencia",
    "R1": "reactiva",
    "R2": "reactiva",
    "R3": "reactiva",
    "R4": "reactiva",
}

magnitud_a_unit = {
    "AE": "kWh",
    "AS": "kWh",
    "PM": "kW",
    "EP": "kW",
    "R1": "kVarh",
    "R2": "kVarh",
    "R3": "kVarh",
    "R4": "kVarh",
}

periode_a_name = {
    "91": "P1",
    "92": "P2",
    "93": "P3",
    "9392": "P2",
    "A1": "P1",
    "A2": "P2",
    "A3": "P3",
    "A4": "P4",
    "A5": "P5",
    "A6": "P6",
}


def get_unit_magnitude(magnitud):
    return magnitud_a_unit.get(magnitud, "eV")


def get_invoice_lines(invoice, magnitud, periode):
    if magnitud == "PM" and periode == "93":
        periode = "9392"

    tipus = magnitud_a_tipus.get(magnitud, None)
    name = periode_a_name.get(periode, None)
    if not name or not tipus:
        return []

    lines = []
    for l in invoice.linia_ids:  # noqa: E741
        if l.name == name and l.tipus == tipus:
            lines.append(l)
    return lines


def to_date(str_date, hours=False):
    if not str_date:
        return None
    if not hours:
        return datetime.strptime(str_date[0:10], "%Y-%m-%d")
    return datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S")


def to_string(obj_date, hours=False):
    if not obj_date:
        return ""
    if not hours:
        return obj_date.strftime("%d-%m-%Y")
    return obj_date.strftime("%d-%m-%Y %H:%M:%S")


def dateformat(str_date, hours=False):
    if not str_date:
        return ""
    if not hours:
        return datetime.strptime(str_date[0:10], "%Y-%m-%d").strftime("%d-%m-%Y")
    return datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")


def get_description(key, table_name, on_error_return_false=False):
    try:
        return gestion_atr_get_description(key, table_name)
    except (ValueError, KeyError):
        if on_error_return_false:
            return False
        return "ERROR {} no trobat a {}.".format(key, table_name)


def is_domestic(pol):
    for cat in pol.category_id:
        if cat.code == "DOM":
            return True
    return False


def is_enterprise(pol):
    return not is_domestic(pol)


def has_category(pol, category_ids):
    for cat in pol.category_id:
        if cat.id in category_ids:
            return True
    return False
