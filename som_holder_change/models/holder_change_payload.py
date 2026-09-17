# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


INDIVIDUAL_VAT_PREFIXES = "0123456789KLMXYZ"
SPECIAL_CASE_DOCUMENT_SPECS = (
    ("reason_death", "holder_change_death", "Certificat defunció"),
    ("reason_merge", "holder_change_merge", "Certificat fusió"),
    ("reason_electrodep", "holder_change_medical", "Justificant mèdic"),
)


def normalize_holder_vat(holder):
    vat = holder["vat"].upper()
    return vat if vat.startswith("ES") else "ES{}".format(vat)


def holder_full_name(holder):
    if not is_individual_holder(holder):
        return holder["name"]
    surnames = holder["surname1"]
    if holder.get("surname2"):
        surnames = "{} {}".format(surnames, holder["surname2"])
    return "{}, {}".format(surnames, holder["name"])


def is_individual_holder(holder):
    return holder["vat"][0].upper() in INDIVIDUAL_VAT_PREFIXES


def clean_iban(iban):
    return "".join(char.upper() for char in iban if char.isalnum())


def append_observation(current, new):
    normalized = "".join(new.split())
    if normalized and normalized in "".join((current or "").split()):
        return current
    return "{}\n{}".format(new, current or "")


def special_case_document_spec(cases):
    for reason, category_code, description in SPECIAL_CASE_DOCUMENT_SPECS:
        if cases.get(reason):
            return category_code, description
    return False, False
