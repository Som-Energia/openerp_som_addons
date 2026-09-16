# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


INDIVIDUAL_VAT_PREFIXES = "0123456789KLMXYZ"


def normalize_holder_vat(holder):
    vat = holder["vat"].upper()
    return vat if vat.startswith("ES") else "ES{}".format(vat)


def is_individual_holder(holder):
    return holder["vat"][0].upper() in INDIVIDUAL_VAT_PREFIXES


def holder_full_name(holder):
    if not is_individual_holder(holder):
        return holder["name"]
    surnames = holder["surname1"]
    if holder.get("surname2"):
        surnames = "{} {}".format(surnames, holder["surname2"])
    return "{}, {}".format(surnames, holder["name"])


def clean_iban(iban):
    return "".join(char.upper() for char in iban if char.isalnum())


def append_observation(current, new):
    normalized = "".join(new.split())
    if normalized and normalized in "".join((current or "").split()):
        return current
    return "{}\n{}".format(new, current or "")
