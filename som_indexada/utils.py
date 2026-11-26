# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals
from giscedata_facturacio.report.utils import get_atr_price
from datetime import date, timedelta
from ast import literal_eval

from .taxes import compute_estimation_taxes


def get_bo_social_estimation(cursor, uid, pol, context=None):
    """Annual financing charge, separate from the energy/power tax base."""
    context = dict(context or {})
    context['date'] = context.get('date') or date.today().strftime('%Y-%m-%d')
    if hasattr(context['date'], 'strftime'):
        context['date'] = context['date'].strftime('%Y-%m-%d')
    conf_obj = pol.pool.get('res.config')
    if not int(conf_obj.get(cursor, uid, 'invoice_active_bo_social', '0')):
        return 0, 0
    start_date = conf_obj.get(
        cursor, uid, 'invoice_start_date_bo_social', '2016-01-01'
    ) or '2016-01-01'
    excluded = literal_eval(conf_obj.get(
        cursor, uid, 'giscedata_exclude_tariff_apply_bo_social', '[]'
    ))
    if context['date'] < start_date or pol.tarifa.name in excluded:
        return 0, 0
    product_id = pol.pool.get('ir.model.data').get_object_reference(
        cursor, uid, 'giscedata_repercusio_bo_social', 'bosocial_BS01'
    )[1]
    product = pol.pool.get('product.product').browse(
        cursor, uid, product_id, context=context
    )
    # Request a daily price even if the product is configured per month/year.
    context['uom'] = pol.pool.get('ir.model.data').get_object_reference(
        cursor, uid, 'giscedata_repercusio_bo_social', 'product_uom_day'
    )[1]
    pricelist_id = context.get('force_pricelist', pol.llista_preu.id)
    price = pol.pool.get('product.pricelist').price_get(
        cursor, uid, [pricelist_id], product_id, 1, context=context
    )[pricelist_id]
    annual = price * 365
    with_taxes, _rates = compute_estimation_taxes(
        cursor, uid, pol, annual, taxes=product.taxes_id, context=context, product=product
    )
    return annual, with_taxes


def get_fs_from_k_change(cursor, uid, pol, context=None):
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
    pricelist_id = context.get('force_pricelist')
    if pricelist_id is None and (pol.modcontractuals_ids
                                 and pol.modcontractuals_ids[0].state == "pendent"
                                 and pol.mode_facturacio
                                 != pol.modcontractuals_ids[0].mode_facturacio
                                 and pol.modcontractuals_ids[0].mode_facturacio == 'index'):
        pricelist_id = pol.modcontractuals_ids[1].llista_preu.id
    elif pricelist_id is None and (pol.modcontractuals_ids
                                   and pol.modcontractuals_ids[0].state == "pendent"
                                   and pol.mode_facturacio
                                   != pol.modcontractuals_ids[0].mode_facturacio
                                   and pol.modcontractuals_ids[0].mode_facturacio == 'atr'):
        pricelist_id = pol.modcontractuals_ids[0].llista_preu.id
    if pricelist_id is None:
        pricelist_id = pol.llista_preu.id
    context["force_pricelist"] = pricelist_id
    for terme, values in periods.items():
        result[terme] = {}
        for periode in values:
            preu_periode = get_atr_price(
                cursor, uid, pol, periode, terme, context=context, with_taxes=with_taxes
            )[0]
            result[terme][periode] = preu_periode

    # Factor K
    try:
        imd_obj = pol.pool.get('ir.model.data')
        pl_obj = pol.pool.get('product.pricelist')
        factor_k = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_indexada', 'product_factor_k')
        price_factor_k = pl_obj.price_get(
            cursor, uid, [pricelist_id], factor_k[1], 1, context=context)
        result['factor_k'] = price_factor_k.get(pricelist_id, 0.0)
    except Exception:
        result['factor_k'] = 0.0
    return result


def calculate_new_indexed_prices(cursor, uid, pol, context=None):
    context = dict(context or {})

    context_preus_antics = dict(context)
    context_preus_antics["date"] = date.today().strftime("%Y-%m-%d")

    context_preus_nous = dict(context)
    context_preus_nous["date"] = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")

    # Compare price dates using the same supplied contract conditions.
    dict_preus_antiga = get_preus(
        cursor, uid, pol, with_taxes=False, context=context_preus_antics
    )

    dict_preus_nova = get_preus(
        cursor, uid, pol, with_taxes=False, context=context_preus_nous
    )

    fs = get_fs_from_k_change(cursor, uid, pol, context=context)

    f_antiga = fs.get('k_old', dict_preus_antiga.get('factor_k', 0))
    f_nova = fs.get('k_new', dict_preus_nova.get('factor_k', 0))

    f_antiga_kwh = f_antiga  # it's already in kwh
    f_nova_kwh = f_nova  # it's already in kwh

    # Preus energia
    indexada_consum_tipus = eval(
        pol.pool.get("res.config").get(cursor, uid, "som_indexada_consum_tipus", "{}"))
    if indexada_consum_tipus == {}:
        raise Exception("No s'han definit els consums tipus per càlculs d'indexació")
    tarifa_acces = pol.tarifa.name
    key_price_name = "preu_sense_F"

    if tarifa_acces not in indexada_consum_tipus:
        raise Exception(
            "La tarifa d'accés %s no té definit un consum tipus per càlculs d'indexació"
            % tarifa_acces
        )
    preu_sense_F = indexada_consum_tipus[tarifa_acces][key_price_name]
    # Keep report averages in EUR/MWh; F is already EUR/kWh.
    preu_mitja_antic = (1.015 * f_antiga_kwh * 1000 + preu_sense_F)
    preu_mitja_nou = (1.015 * f_nova_kwh * 1000 + preu_sense_F)

    conany = pol.cups.conany_kwh if pol.cups.conany_kwh > 0 else 1

    import_energia_anual_antiga = (preu_mitja_antic / 1000) * conany
    import_energia_anual_nova = (preu_mitja_nou / 1000) * conany

    # Preus potència
    potencia = pol.potencia
    dict_potencies_pol = {p.periode_id.name: p.potencia for p in pol.potencies_periode}

    dict_preu_potencia_antiga = dict_preus_antiga['tp']
    preu_potencia_antiga = 0
    for k in dict_preu_potencia_antiga.keys():
        preu_potencia_antiga += dict_potencies_pol.get(k, 0) * dict_preu_potencia_antiga.get(k, 0)

    dict_preu_potencia_nova = dict_preus_nova['tp']
    preu_potencia_nova = 0
    for k in dict_preu_potencia_nova.keys():
        preu_potencia_nova += dict_potencies_pol.get(k, 0) * dict_preu_potencia_nova.get(k, 0)

    import_potencia_anual_antiga = preu_potencia_antiga
    import_potencia_anual_nova = preu_potencia_nova

    bo_social_antiga, bo_social_antiga_imp = get_bo_social_estimation(
        cursor, uid, pol, context=context_preus_antics
    )
    bo_social_nova, bo_social_nova_imp = get_bo_social_estimation(
        cursor, uid, pol, context=context_preus_nous
    )
    base_antiga = import_energia_anual_antiga + import_potencia_anual_antiga
    base_nova = import_energia_anual_nova + import_potencia_anual_nova
    import_total_anual_antiga = base_antiga + bo_social_antiga
    import_total_anual_nova = base_nova + bo_social_nova

    impacte_import = import_total_anual_nova - import_total_anual_antiga
    impacte_perc = impacte_import / import_total_anual_antiga if import_total_anual_antiga else 0

    base_antiga_imp, taxes_antiga = compute_estimation_taxes(
        cursor, uid, pol, base_antiga, context=context_preus_antics
    )
    base_nova_imp, taxes_nova = compute_estimation_taxes(
        cursor, uid, pol, base_nova, context=context_preus_nous
    )
    import_total_anual_antiga_amb_impost = base_antiga_imp + bo_social_antiga_imp
    import_total_anual_nova_amb_impost = base_nova_imp + bo_social_nova_imp

    impacte_import_amb_impost = (
        import_total_anual_nova_amb_impost - import_total_anual_antiga_amb_impost
    )
    impacte_perc_amb_impost = (
        impacte_import_amb_impost / import_total_anual_antiga_amb_impost
        if import_total_anual_antiga_amb_impost else 0
    )

    dades_index = {
        "iva": taxes_nova.get('IGIC', taxes_nova.get('IVA', 0)) * 100,
        "ie": taxes_nova.get('IE', 0) * 100,
        "impostos_antiga": taxes_antiga,
        "impostos_nova": taxes_nova,
        "conany": conany,
        "pot_contractada": potencia,
        "preu_sense_F": preu_sense_F,
        "f_antiga": f_antiga,
        "f_nova": f_nova,
        "f_antiga_kwh": f_antiga_kwh,
        "f_nova_kwh": f_nova_kwh,
        "preu_mig_anual_antiga": preu_mitja_antic,
        "preu_mig_anual_nova": preu_mitja_nou,
        "import_potencia_anual_antiga": import_potencia_anual_antiga,
        "import_potencia_anual_nova": import_potencia_anual_nova,
        "import_energia_anual_antiga": import_energia_anual_antiga,
        "import_energia_anual_nova": import_energia_anual_nova,
        "import_bo_social_anual_antiga": bo_social_antiga,
        "import_bo_social_anual_nova": bo_social_nova,
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
