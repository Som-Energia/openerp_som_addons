# -*- coding: utf-8 -*-
# SCRIPT EN PYTHON 3 

from datetime import datetime
from erppeek import Client
import os
import dbconfig

try:
    from StringIO import StringIO  # for Python 2
except ImportError:
    from io import StringIO  # for Python 3
import csv

root_dir = '/mnt/nfs/factures'
START_DATE = '2021-06-01'


def write_csv(report, header, filename):
    csv_doc = StringIO()
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
                line.append("error")
    return line


def write_csv_factura(c, fact_ids, filename):
    fields = ['id', 'number', 'energia_kwh', ['rectifying_id', 1], 'rectifying_id.energia_kwh', [
        'polissa_id', 1], ['cups_id', 1], 'data_inici', 'data_final']
    header = ['id', 'number', 'energia_kwh', 'rectifying_id',
              'rectifying_id.energia_kwh', 'polissa_id', 'cups_id', 'data_inici', 'data_final']
    result = []
    for data in c.GiscedataFacturacioFactura.read(fact_ids, header):
        for field in header:
            if field not in data:
                fact = c.GiscedataFacturacioFactura.browse(get_gff_id(c, data['rectifying_id'][0]))
                if fact.rectifySing_id:
                    data['rectifying_id.energia_kwh'] = fact.energia_kwh
        result.append(parse_csv_line(fields, data))

    write_csv(result, header, filename)


def write_csv_polissa(c, pol_ids, filename):
    fields = ['id', 'name', 'data_alta', 'active', 'state']
    header = fields
    result = []
    for data in c.GiscedataPolissa.read(pol_ids, fields):
        result.append(parse_csv_line(fields, data))

    write_csv(result, header, filename)


def get_pdf_files(root_dir):
    pdf_files = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.pdf'):
                pdf_files.append(file)
    return pdf_files


def count_directories(directory_path):
    try:
        # Llistar tots els elements del directori
        items = os.listdir(directory_path)

        # Comptar quants elements són carpetes
        num_directories = sum(1 for item in items if os.path.isdir(
            os.path.join(directory_path, item)))

        return num_directories
    except Exception as e:
        print(f"Hi ha hagut un error: {e}")
        return 0


def obtenir_factures_refacturades_sobrestimades(O, fact_ids):
    sobrestimades_ids = []
    total_sobrestimat = 0
    for fact in O.GiscedataFacturacioFactura.browse(fact_ids):
        if fact.energia_kwh < fact.ref.energia_kwh:
            sobrestimades_ids.append(fact_ids)
            total_sobrestimat += fact.ref.energia_kwh - fact.energia_kwh
    return sobrestimades_ids, total_sobrestimat


def obtenir_factures_refacturades(O, fact_ids):
    refact_ids = []
    for inv_id in fact_ids:
        gff_id = get_gff_id(O, inv_id)
        fact = O.GiscedataFacturacioFactura.browse(gff_id)
        if fact.refund_by_id:
            gff_ids = O.GiscedataFacturacioFactura.search(
                [('rectifying_id', '=', fact.invoice_id.id)])
            for gff_id in gff_ids:
                tipo = O.GiscedataFacturacioFactura.read(gff_id, ['tipo_rectificadora'])[
                    'tipo_rectificadora']
                if tipo == 'R':
                    refact_ids.append(gff_id)
                    break
    return refact_ids


def get_gff_id(O, inv_id):
    return O.GiscedataFacturacioFactura.search([('invoice_id', '=', inv_id)])[0]


def obtenir_subministres_actius_periode(O, data_inici, data_final):
    pol_ids = O.GiscedataPolissa.search(
        [
            ('data_alta', '<=', data_final),
            '|',
            ('data_baixa', '=', None),
            ('data_baixa', '>', data_inici)
        ], context={'active_test': False})

    cups_ids = set(cups['cups'][0] if cups['cups']
                   else 0 for cups in O.GiscedataPolissa.read(pol_ids, ['cups']))
    cups_ids.pop()
    return len(cups_ids)


O = Client(**dbconfig.erppeek)

pdf_files = get_pdf_files(root_dir)
invoice_numbers = [os.path.splitext(file)[0] for file in pdf_files]
sense_r = []
nomes_a = []
amb_a_r = []
for invoice_number in invoice_numbers:
    inv_id = O.AccountInvoice.search([('number', '=', invoice_number)])
    inv_rect_id = O.AccountInvoice.search([('rectifying_id', '=', inv_id)])
    #print("{} - {}".format(invoice_number, O.AccountInvoice.read(inv_rect_id, ['number'])))
    if len(inv_rect_id) == 0:
        sense_r.append(inv_id)
    elif len(inv_rect_id) == 1:
        nomes_a.append(inv_id)
    else:
        amb_a_r.append(inv_id)


#print("{} que no s'ha fet res".format(sense_r))
#print("{} només abonadores".format(nomes_a))
#print("{} amb abonadora i rectificadora".format(amb_a_r))

llista_factures_refacturades = obtenir_factures_refacturades(O, amb_a_r)
sobrestimades_ids, total_sobrestimat = obtenir_factures_refacturades_sobrestimades(
    O, llista_factures_refacturades)
llista_polisses = count_directories(root_dir)
ncontractes_actius = obtenir_subministres_actius_periode(
    O, START_DATE, datetime.today().strftime('%Y-%m-%d'))
percentatge_estimats = round(llista_polisses * 100.0 / ncontractes_actius, 2)

print("Nombre de factures amb lectures estimades {}".format(len(amb_a_r)))
print(u"Percentatge de contractes amb alguna estimació respecte totals: {}%".format(percentatge_estimats))  # noqa: E501
nrefacturades = len(llista_factures_refacturades)
print(u"Nombre de factures refacturades: {}".format(nrefacturades))
print(u"Nombre de factures refacturades sobrestimades: {}".format(
    len(sobrestimades_ids)))
print(u"Total kwh sobrestimats: {}".format(round(total_sobrestimat)))

write_csv_factura(O, llista_factures_refacturades, 'llista_factures_refacturades.csv')
