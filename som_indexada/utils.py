# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from giscedata_facturacio.report.utils import get_atr_price
from datetime import date, timedelta


indexada_consum_tipus = {
    "2.0TD": {
        "preu_sense_F": 137.5486987,
    },
    "3.0TD": {
        "preu_sense_F": 121.0485735,
    },
    "6.1TD": {
        "preu_sense_F": 105.7246103,
    },
    "3.0TDVE": {
        "preu_sense_F": 0,
    },
}


def get_fs(cursor, uid, pol, context=None):
    if context is None:
        context = {}

    som_polissa_k_change_obj = pol.pool.get("som.polissa.k.change")

    search_params = [
        ('polissa_id', '=', pol.id),
    ]

    if context.get('partner_id', False):
        search_params = [
            ('partner_id', '=', context['partner_id']),
        ]

    k_change_id = som_polissa_k_change_obj.search(
        cursor, uid, search_params, context=context
    )

    res = {}
    if k_change_id:
        res = som_polissa_k_change_obj.read(
            cursor, uid, k_change_id[0], ['k_old', 'k_new'], context=context
        )

    return res


def get_preus(cursor, uid, pol, with_taxes=False, context=None):
    if context is None:
        context = {}
    context["potencia_anual"] = True

    result = {}
    periods = {
        "tp": sorted(pol.tarifa.get_periodes("tp", context=context).keys()),
        "te": sorted(pol.tarifa.get_periodes("te", context=context).keys()),
    }
    if (pol.modcontractuals_ids[0].state == "pendent"
        and pol.mode_facturacio
        != pol.modcontractuals_ids[0].mode_facturacio
            and pol.modcontractuals_ids[0].mode_facturacio == 'index'):
        context["force_pricelist"] = pol.modcontractuals_ids[1].llista_preu.id
    elif(pol.modcontractuals_ids[0].state == "pendent"
            and pol.mode_facturacio
            != pol.modcontractuals_ids[0].mode_facturacio
            and pol.modcontractuals_ids[0].mode_facturacio == 'atr'):
        context["force_pricelist"] = pol.modcontractuals_ids[0].llista_preu.id
    for terme, values in periods.items():
        result[terme] = {}
        for periode in values:
            preu_periode = get_atr_price(
                cursor, uid, pol, periode, terme, context=context, with_taxes=with_taxes
            )[0]
            result[terme][periode] = preu_periode
    return result


def calculate_new_indexed_prices(cursor, uid, pol, context=None):
    if context is None:
        context = {}

    fs = get_fs(cursor, uid, pol, context=context)

    f_antiga = fs.get('k_old', 0)
    f_nova = fs.get('k_new', 0)

    # Preus energia
    tarifa_acces = pol.tarifa.name
    key_price_name = "preu_sense_F"
    preu_sense_F = indexada_consum_tipus[tarifa_acces][key_price_name]
    preu_mitja_antic = (1.015 * f_antiga + preu_sense_F)
    preu_mitja_nou = (1.015 * f_nova + preu_sense_F)

    conany = pol.cups.conany_kwh if pol.cups.conany_kwh > 0 else 1

    import_energia_anual_antiga = (preu_mitja_antic / 1000) * conany
    import_energia_anual_nova = (preu_mitja_nou / 1000) * conany

    # Preus potència
    context_preus_antics = dict(context)
    context_preus_antics["date"] = date.today().strftime("%Y-%m-%d")

    context_preus_nous = dict(context)
    context_preus_nous["date"] = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")

    potencia = pol.potencia
    dict_potencies_pol = {p.periode_id.name: p.potencia for p in pol.potencies_periode}

    dict_preus_potencia_antiga = get_preus(
        cursor, uid, pol, with_taxes=False, context=context_preus_antics
    )
    dict_preu_potencia_antiga = dict_preus_potencia_antiga['tp']
    preu_potencia_antiga = 0
    for k in dict_preu_potencia_antiga.keys():
        preu_potencia_antiga += dict_potencies_pol.get(k, 0) * dict_preu_potencia_antiga.get(k, 0)

    dict_preus_potencia_nova = get_preus(
        cursor, uid, pol, with_taxes=False, context=context_preus_nous
    )
    dict_preu_potencia_nova = dict_preus_potencia_nova['tp']
    preu_potencia_nova = 0
    for k in dict_preu_potencia_nova.keys():
        preu_potencia_nova += dict_potencies_pol.get(k, 0) * dict_preu_potencia_nova.get(k, 0)

    import_potencia_anual_antiga = preu_potencia_antiga
    import_potencia_anual_nova = preu_potencia_nova

    # Imports totals
    import_total_anual_antiga = import_energia_anual_antiga + import_potencia_anual_antiga
    import_total_anual_nova = import_energia_anual_nova + import_potencia_anual_nova

    impacte_import = import_total_anual_nova - import_total_anual_antiga
    impacte_perc = impacte_import / import_total_anual_antiga

    # Nota: 1.0511 * 1.21 és el factor per impostos (IE + IVA)
    import_total_anual_antiga_amb_impost = import_total_anual_antiga * 1.0511 * 1.21
    import_total_anual_nova_amb_impost = import_total_anual_nova * 1.0511 * 1.21

    impacte_import_amb_impost = (
        import_total_anual_nova_amb_impost - import_total_anual_antiga_amb_impost
    )
    impacte_perc_amb_impost = impacte_import_amb_impost / import_total_anual_antiga_amb_impost

    dades_index = {
        "iva": 21,
        "ie": 5.11,
        "conany": conany,
        "pot_contractada": potencia,
        "preu_sense_F": preu_sense_F,
        "f_antiga": f_antiga,
        "f_nova": f_nova,
        "preu_mig_anual_antiga": preu_mitja_antic,
        "preu_mig_anual_nova": preu_mitja_nou,
        "import_potencia_anual_antiga": import_potencia_anual_antiga,
        "import_potencia_anual_nova": import_potencia_anual_nova,
        "import_energia_anual_antiga": import_energia_anual_antiga,
        "import_energia_anual_nova": import_energia_anual_nova,
        "import_total_anual_antiga": import_total_anual_antiga,
        "import_total_anual_nova": import_total_anual_nova,
        "impacte_import": impacte_import,
        "impacte_perc": impacte_perc * 100,
        "import_total_anual_antiga_amb_impost": import_total_anual_antiga_amb_impost,
        "import_total_anual_nova_amb_impost": import_total_anual_nova_amb_impost,
        "impacte_import_amb_impost": impacte_import_amb_impost,
        "impacte_perc_amb_impost": impacte_perc_amb_impost * 100,
    }

    return dades_index
