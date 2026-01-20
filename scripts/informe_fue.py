# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import dbconfig
from consolemsg import step, success, warn
from erppeek import Client
from tqdm import tqdm
import psycopg2
import StringIO
import csv

"""_summary_
Dades per informe FUE sobre les refacturacions
1.- Hem tingut en compte les factures amb lectures Estimades (estmació distri codi 40) i estimació comer 'ES'.  # noqa: E501
2.- A efectes de refacturació, considerem només les factures tipus "R"
3.- Per obentir el marge d'error en les estimacions, només sumem les refacturacions on hem hagut de tornar dines (no fem res amb les infraestimacions)  # noqa: E501
4.- Considerem que la distri no ens esta enviant lectures quan han passat 2 mesos des de la darrera lectura  # noqa: E501

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

# Estimacions a tenir en compte
# CALCULADA_SOM = [('LC', 'ES')] # Calculada Som
# CALCULADA_DISTRI = [('LC', '')] # Calculada Distri
# ESTIMACIO_SOM = [('40', 'ES'), ('99', 'ES')] # Estimada Som Energia

ESTIMACIO_DISTRI = [7, 10, 11]  # Estimada
ESTIMACIO_SOM = 'ES'  # Estimada Som Energia

START_DATE = '2021-06-01'

DATA_FALTEN_LECTURES = (datetime.today() - timedelta(days=62)).strftime('%Y-%m-%d')
DATA_FALTEN_LECTURES = '2023-01-01'

TOTS_CONTRACTES = 'True'  # En cas de canvi de titular, comptem 2 contractes


def write_csv(report, header, filename):
    csv_doc = StringIO.StringIO()
    writer_report = csv.writer(csv_doc, delimiter=';')
    writer_report.writerow(header)
    writer_report.writerows(report)
    doc = csv_doc.getvalue()
    with open(filename, 'w') as f:
        f.write(doc)


def parse_csv_line(fields, data, error='Err'):
    line = []
    for field in fields:
        if type(field) == str:
            line.append(data.get(field, error))
        elif type(field) == list and len(field) == 2:
            val = data.get(field[0], [])
            if type(val) == list and len(val) == field[1] + 1:
                line.append(val[field[1]])
            else:
                line.append(error)
    return line


def write_csv_factura(c, fact_ids, filename):
    fields = ['id', 'number', ['polissa_id', 1], 'data_inici', 'data_final']
    header = ['id', 'number', 'polissa_id', 'data_inici', 'data_final']
    result = []
    for data in c.GiscedataFacturacioFactura.read(fact_ids, header):
        result.append(parse_csv_line(fields, data))

    write_csv(result, header, filename)


def write_csv_polissa(c, pol_ids, filename):
    fields = ['id', 'name', 'data_alta', 'active', 'state']
    header = fields
    result = []
    for data in c.GiscedataPolissa.read(pol_ids, fields):
        result.append(parse_csv_line(fields, data))

    write_csv(result, header, filename)


def get_db_cursor():
    try:
        dbconn = psycopg2.connect(**dbconfig.psycopg)
    except Exception, ex:
        warn("Unable to connect to database {}", str(dbconfig.psycopg))
        raise ex

    return dbconn.cursor()


def execute_sql(dbcur, sql_query):
    try:
        dbcur.execute(sql_query)
    except Exception, ex:
        warn('Failed executing query')
        warn(sql_query)
        raise ex

    return [record[0] for record in dbcur.fetchall()]


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


def contractes_estimats_no_refactures(cur):
    sql = """
        select distinct gp.id
        from
        giscedata_polissa gp ,
        giscedata_cups_ps gcp,
        res_municipi rm,
        giscedata_facturacio_factura gff ,
        account_invoice ai,
        giscedata_lectures_lectura gll ,
        giscedata_lectures_comptador glc
        where
        gp.id = gff.polissa_id and
        gcp.id = gp.cups and
        gcp.id_municipi = rm.id and
        rm.state in (9, 20, 28, 45) and
        ai.id = gff.invoice_id and
        glc.polissa = gp.id and
        gll.comptador = glc.id and
        gll.name = gff.data_final and
        gp.active = true and
        gp.state = 'activa' and
        gll.origen_id in (7,10,11) and
        gll.origen_comer_id = 6 and
        gff.id =
            (select max(gff2.id)
            from giscedata_facturacio_factura gff2
            where gff2.polissa_id = gp.id
            ) and
        ai."type" = 'out_invoice' and
        ai.rectifying_id is null
    """
    pol_ids = execute_sql(cur, sql)
    """
    erppeek
    pol_ids = []
    for pol_id in c.GiscedataPolissa.search([]):
        pol = c.GiscedataPolissa.read(pol_id, ['data_ultima_factura'])
        f_ids = c.GiscedataFacturacioFactura.search(
            [('polissa_id','=', pol_id),
             ('date_invoice','=', pol['data_ultima_factura']),
             ('type','=','out_invoice'),
             ('rectifying_id', "=", False)])
        if not f_ids:
            continue
        fact = c.GiscedataFacturacioFactura.read(f_ids[0], ['comptadors', 'data_final'])
        l_ids = c.GiscedataLecturesLectura.search(
            [('comptador', '=', fact['comptadors'][0]),
             ('name','=',fact['data_final']),
             ('origen_id','in', [7, 10, 11]),
             ('origen_comer_id','=', 6)])
        if not l_ids:
            continue
        pol_ids.append(pol_id)"""

    return len(pol_ids)


def contractes_sense_lectures_distri(c):
    return len(c.GiscedataPolissa.search(
        [('data_ultima_lectura', '<', DATA_FALTEN_LECTURES)]))


def main():
    c = Client(**dbconfig.erppeek)
    cur = get_db_cursor()

    contractes_estimats_no_refactures(cur)
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
    ncontractes_sense_lectures = contractes_sense_lectures_distri(c)
    step(u"Nombre de contractes sense lectures distri (2 mesos): {}".format(ncontractes_sense_lectures))  # noqa: E501
    success(u"Feina feta.")


if __name__ == "__main__":
    main()
