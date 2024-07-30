# -*- coding: utf-8 -*-
from datetime import datetime
import dbconfig
from consolemsg import step, success
from erppeek import Client
from tqdm import tqdm
<<<<<<< HEAD
=======


"""_summary_
Dades per informe FUE sobre les refacturacions


SQL per trobar factures en aquest estat:

SELECT distinct
  gff.id
FROM
  public.giscedata_lectures_lectura gll,
  public.giscedata_facturacio_lectures_energia gfle,
  public.giscedata_facturacio_factura gff,
  public.account_invoice ai
where
  gll.comptador = gfle.comptador_id and
  gfle.data_actual = gll.name and
  gff.invoice_id = ai.id and
  gff.id = gfle.factura_id and
  gll.name > '2021-06-01' and
  gll.origen_id = 7 and
  gll.origen_comer_id = 6 and
  ai.refund_by_id is not null
LIMIT
  10
"""
>>>>>>> f8e20179 (Change browse for read to speed script)

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
        [('data_actual', '>=', START_DATE),
         ('origen_id', 'in', ESTIMACIO_DISTRI)]
    )
    for lect_facura_id in tqdm(lect_factura_ids):
        # Prova amb origen_comer_lectura_id 24291945)
        # fact_ids.extend([20023375,19048105,14234080,14765367,14822753,14889180,14889205,14889225,15687351,15738936,15868910])  # noqa: E501
        # break
        lect_factura = c.GiscedataFacturacioLecturesEnergia.read(
            lect_facura_id, ['comptador_id', 'data_actual', 'factura_id'])
        llista_lectures = c.GiscedataLecturesLectura.search(
            [('comptador', '=', lect_factura['comptador_id'][0]),
             ('name', '=', lect_factura['data_actual'])], limit=1)
        if not llista_lectures:
            continue
        origen_comer_lectura = c.GiscedataLecturesLectura.read(
            llista_lectures[0], ['origen_comer_id'])['origen_comer_id'][0]
        if origen_comer_lectura != ESTIMACIO_SOM:
            # Es estimada de Distri
            continue

        fact_ids.append(lect_factura['factura_id'][0])

    return fact_ids


def obtenir_polisses_llista_factures(c, fact_ids):
    if not fact_ids:
        return []
    pol_ids = []
    llista = c.GiscedataFacturacioFactura.read(fact_ids, ['polissa_id'])
    for fact in llista:
        if fact['polissa_id'][0] in pol_ids:
            continue
        pol_ids.append(fact['polissa_id'][0])
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
                [('rectifying_id', '=', fact.invoice_id.id)])
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
        c, START_DATE, datetime.today().strftime('%Y-%m-%d'))
    step(u"Nombre de contractes actius des del {}:  {}".format(START_DATE, ncontractes_actius))
    percentatge_estimats = round(len(llista_polisses) * 100.0 / ncontractes_actius, 2)
    step(u"Percentatge de contractes amb alguna estimació respecte totals: {}%".format(percentatge_estimats))  # noqa: E501
    llista_factures_refacturades = obtenir_factures_refacturades(c, llista_factures)
    nrefacturades = len(llista_factures_refacturades)
    step(u"Nombre de factures refacturades: {}".format(nrefacturades))
    llista_factures_refacturades_sobrestimades, total_sobrestimat = obtenir_factures_refacturades_sobrestimades(  # noqa: E501
        c, llista_factures_refacturades)
    step(u"Nombre de factures refacturades sobrestimades: {}".format(
        len(llista_factures_refacturades_sobrestimades)))
    step(u"Total kwh sobrestimats: {}".format(total_sobrestimat))

    success(u"Feina feta.")


if __name__ == "__main__":
    main()
