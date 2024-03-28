# -*- coding: utf-8 -*-

# Pas 1: Executar script
# PYTHONIOENCODING="UTF-8" PYTHONPATH="$OPENERP_ROOT_PATH:$OPENERP_ADDONS_PATH:$HOME/src/erp/server/sitecustomize" python andalucia.py  # noqa: E501

# Pas 2: Canviar dates sortida (Regex VSCode)
# (\d+)-(\d+)-(\d+)
# $1$2$3

# Pas 3: Canviar punts per comes als números de la sortida (Regex VSCode)
# ;(\d+)\.
# ;$1,
# ;-(\d+)\.
# ;-$1,

# Pas 4: Cntl+C Cntl+V del CSV a l'Excel
# La columna del nom de pòlissa donar-li format text per mantenir els 0

from collections import OrderedDict

import csv
import configdb
from erppeek import Client

csv_reader = False

data_dict_list = []
output = []

# Read CSV
with open('input_vat.csv', mode='r') as file:
    csv_reader = csv.DictReader(file)

    for row in csv_reader:
        data_dict_list.append(row)

# Connect to ERP
c = Client(**configdb.erppeek)

pol_obj = c.model('giscedata.polissa')
fact_obj = c.model('giscedata.facturacio.factura')

for data_dict in data_dict_list:
    vat = data_dict['vat']
    pol_ids = pol_obj.search(
        [('titular_nif', 'like', '%' + vat)],
        context={'active_test': False},
    )
    print("NIF {}: {} contracts".format(vat, len(pol_ids)))
    polisses = pol_obj.browse(pol_ids)
    for pol in polisses:
        fact_ids = fact_obj.search([
            ('polissa_id', '=', pol.id),
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('data_final', '>=', '2021-01-01'),
            ('data_inici', '<=', '2022-12-31'),
        ])
        print("    NIF {}: POL {}: {} factures".format(vat, pol.name, len(fact_ids)))
        factures = fact_obj.browse(fact_ids)
        for fact in factures:
            fact_line = OrderedDict()
            fact_line['tipo_registro_2'] = '2'
            fact_line['nif'] = vat
            fact_line['nombre'] = data_dict['name'].encode('utf-8')
            fact_line['contrato'] = pol.name
            fact_line['tipo_via'] = ''
            fact_line['direccio'] = pol.cups_direccio.encode('utf-8')
            fact_line['tipo_numeracion'] = 'NUM'
            fact_line['numero'] = ''
            fact_line['calificador_numero'] = ''
            fact_line['bloque'] = ''
            fact_line['portal'] = ''
            fact_line['escalera'] = ''
            fact_line['planta'] = ''
            fact_line['puerta'] = ''
            fact_line['complemento'] = ''
            fact_line['poblacion'] = ''
            fact_line['municipio'] = ''
            fact_line['codigo_municipio'] = ''
            fact_line['codigo_provincia'] = ''
            fact_line['codigo_postal'] = ''
            fact_line['cups'] = pol.cups.name
            fact_line['fecha_alta'] = pol.data_alta
            fact_line['fecha_baja'] = pol.data_baixa if pol.data_baixa else ''
            fact_line['tipo_registro_3'] = '3'
            fact_line['num_factura'] = fact.number
            fact_line['fecha_emision'] = fact.date_invoice
            fact_line['fecha_inicio'] = fact.data_inici
            fact_line['fecha_final'] = fact.data_final
            fact_line['dias'] = fact.dies
            fact_line['pagado'] = fact.state
            fact_line['fecha_pago'] = fact.date_due
            if not fact.lectures_energia_ids:
                fact_line['tipo_lectura'] = ''
            else:
                fact_line['tipo_lectura'] = 'E' if fact.lectures_energia_ids[0].origen_id.codi in [
                    '40', 'LC'] else 'R'

            # Girar signe out_refund
            signe = 1
            if fact.type == 'out_refund':
                signe = -1
            fact_line['consumo_facturado'] = fact.energia_kwh * signe
            fact_line['importe_energia'] = (fact.amount_total - (
                fact.total_altres + fact.total_lloguers + fact.amount_tax)) * signe
            fact_line['importe_servicios'] = (fact.total_altres + fact.total_lloguers) * signe
            fact_line['impuestos'] = fact.amount_tax * signe
            fact_line['total_factura'] = fact.amount_total * signe

            fact_line['tipo_registro_4'] = '4'
            fact_line['nif_sol'] = vat
            fact_line['nombre_sol'] = data_dict['name'].encode('utf-8')
            fact_line['codigo_error'] = ''
            fact_line['motivo_error'] = ''
            output.append(fact_line)
    # break

with open('output_data.csv', 'w') as csv_file:
    escritor_csv = csv.DictWriter(csv_file, fieldnames=output[0].keys(), delimiter=';')
    escritor_csv.writeheader()

    for fila in output:
        escritor_csv.writerow(fila)
