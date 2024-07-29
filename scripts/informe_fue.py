# -*- coding: utf-8 -*-
from datetime import datetime
import dbconfig
from consolemsg import step, success
from erppeek import Client

# Estimacions a tenir en compte
# CALCULADA_SOM = [('LC', 'ES')] # Calculada Som
# CALCULADA_DISTRI = [('LC', '')] # Calculada Distri
# ESTIMACIO_SOM = [('40', 'ES'), ('99', 'ES')] # Estimada Som Energia

ESTIMACIO_DISTRI = [7, 10, 11]  # Estimada
ESTIMACIO_SOM = 'ES'  # Estimada Som Energia

START_DATE = '2021-06-01'

TOTS_CONTRACTES = 'True'  # En cas de canvi de titular, comptem 2 contractes


def obtenir_llista_factures_estimades_som(c):
    fact_ids = []
    lect_factura_ids = c.GiscedataFacturacioLecturesEnergia.search(
        [('data_actual', '>=', '2021-06-01'),
         ('origen_id', 'in', ESTIMACIO_DISTRI)]
    )
    for lect_facura_id in lect_factura_ids:
        lect_factura = c.GiscedataFacturacioLecturesEnergia.browse(lect_facura_id)
        llista_lectures = c.GiscedataLecturesLectura.search(
            [('comptador', '=', lect_factura.comptador_id.id),
             ('name', '=', lect_factura.data_actual)])
        if not llista_lectures:
            continue
        origen_comer_lectura_id = c.GiscedataLecturesLectura.read(
            llista_lectures[0], ['origen_comer_id'])
        if origen_comer_lectura_id != ESTIMACIO_SOM:
            # Es estimada de Distri
            continue
        fact_ids.append(lect_factura.factura_id.id)

    return fact_ids


def obtenir_polisses_llista_factures(c, fact_ids):
    pol_ids = []
    for fact in c.GiscedataFacturacioFactura.browse(fact_ids):
        if fact.polissa_id.id in pol_ids:
            continue
        pol_ids.append(fact.polissa_id.id)
    return pol_ids


def obtenir_contractes_actius_periode(c, data_inici, data_final):
    pol_ids = c.GiscedataPolissa.search(
        [
            ('data_alta', '<=', data_final),
            '|',
            ('data_baixa', '=', None),
            ('data_baixa', '>', data_inici)
        ], context={'active_test': False})

    return len(pol_ids)


def obtenir_factures_refacturades(c, fact_ids):
    refact_ids = []
    for fact in c.GiscedataFacturacioFactura.browse(fact_ids):
        if fact.refund_by_id:
            gff_ids = c.GiscedataFacturacioFactura.search(
                [('rectifying_id', '=', fact.refund_by_id.id)])
            for gff_id in gff_ids:
                tipo = c.GiscedataFacturacioFactura.read(gff_id, ['tipo_rectificadora'])[
                    'tipo_rectificadora']
                if tipo == 'R':
                    refact_ids.append(gff_id)
                    break
    return refact_ids


def obtenir_factures_refacturades_sobrestimades(c, fact_ids):
    sobrestimades_ids = []
    total_sobrestimat = 0
    for fact in c.GiscedataFacturacioFactura.browse(fact_ids):
        if fact.energia_kwh < fact.ref.energia_kwh:
            sobrestimades_ids.append(fact_ids)
            total_sobrestimat += fact.ref.energia_kwh - fact.energia_kwh
    return sobrestimades_ids, total_sobrestimat


def main():
    c = Client(**dbconfig.erppeek)
    step(u"Obtenim factures")
    llista_factures = obtenir_llista_factures_estimades_som(c)
    step(u"Nombre de factures amb lectures estimades:  {}".format(len(llista_factures)))
    llista_polisses = obtenir_polisses_llista_factures(c, llista_factures)
    step(u"Nombre de contractes amb factures amb lectures estimades:  {}".format(len(llista_polisses)))  # noqa: E501
    ncontractes_actius = obtenir_contractes_actius_periode(
        c, '2021-06-01', datetime.today().strftime('%Y-%m-%d'))
    step(u"Nombre de contractes actius des del {}:  {}".format(START_DATE, ncontractes_actius))
    step(u"Percentatge de contractes amb alguna estimació respecte totals: {}".format(
        len(llista_polisses) * 100 / ncontractes_actius))
    llista_factures_refacturades = obtenir_factures_refacturades(c, llista_factures)
    nrefacturades = len(llista_factures_refacturades)
    step(u"Nombre de factures refacturades: {}".format(nrefacturades))
    llista_factures_refacturades_sobrestimades, total_sobrestimat = obtenir_factures_refacturades_sobrestimades(  # noqa: E501
        c, llista_factures_refacturades)
    step(u"Nombre de factures refacturades sobrestimades: {}".format(nrefacturades))
    step(u"Total kwh sobrestimats: {}".format(total_sobrestimat))

    success(u"Feina feta.")


if __name__ == "__main__":
    main()
