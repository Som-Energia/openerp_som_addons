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


from tqdm import tqdm
import csv
import configdb
from erppeek import Client

csv_reader = False

data_dict_list = []
data_dict_list_new = []

output = []

# Read CSV
with open('input_invoices.csv', mode='r') as file:
    csv_reader = csv.DictReader(file)

    for row in csv_reader:
        data_dict_list.append(row)

# Connect to ERP
c = Client(**configdb.erppeek)

pol_obj = c.model('giscedata.polissa')
fact_obj = c.model('giscedata.facturacio.factura')

for data_dict in tqdm(data_dict_list):
    invoice_num = data_dict['Nº FACTURA']
    fact_ids = fact_obj.search([
        ('number', '=', invoice_num),
    ])[0]

    fact = fact_obj.browse(fact_ids)
    # Girar signe out_refund
    signe = 1
    if fact.type == 'out_refund':
        signe = -1
    data_dict['CONSUMO FACTURADO (KWh)'] = fact.energia_kwh * signe

    # Tema imports
    taxes = {}
    for tax in fact.tax_line:
        if tax.tax_id.description and 'IESE' in tax.tax_id.description:
            taxes['IESE'] = tax

    import_energia = 0
    import_factura = fact.amount_total * signe
    if not taxes:
        import_energia = 'OJO: IESE NO TROBAT'
    elif taxes['IESE'].tax_id.name == u'Impuesto especial sobre la electricidad':
        import_energia = (fact.amount_total - (
            fact.total_altres + fact.total_lloguers + fact.amount_tax)) * signe
    elif taxes['IESE'].tax_id.name == u'Impuesto especial sobre la electricidad RD 17/21':
        import_energia = taxes['IESE'].base_amount
    elif taxes['IESE'].tax_id.name == u'Impuesto especial sobre la electricidad Art.99.2 1€/MWh':
        import_energia = round((fact.amount_total - (fact.total_lloguers
                               + fact.amount_tax + float(taxes['IESE'].base))) * signe, 2)
    else:
        import_energia = 'OJO: IESE DIFERENT'

    data_dict['IMPORTE ENERGÍA'] = import_energia
    data_dict['IMPORTE TOTAL DE LA FACTURA'] = import_factura
    if taxes:
        data_dict['IESE'] = taxes['IESE'].tax_id.name.encode('utf-8')
    else:
        data_dict['IESE'] = 'OJO: IESE NO TROBAT'
    data_dict_list_new.append(data_dict)


with open('output_data_new.csv', 'w') as csv_file:
    fieldnames = ['TIPO DE SUMINISTRO', 'CIF COMERCIALIZADORA', 'COMERCIALIZADORA', 'N.I.F. DEL SOLICITANTE', 'CONTRATO DE SUMINISTRO', 'CUPS', 'Nº FACTURA', 'FECHA DE EMISIÓN DE FACTURA',  # noqa: E501
                  'FECHA DE INICIO PERÍODO DE FACTURACIÓN', 'FECHA DE FIN PERÍODO DE FACTURACIÓN', 'CONSUMO FACTURADO (KWh)', 'IMPORTE ENERGÍA', 'IMPORTE TOTAL DE LA FACTURA', 'IESE']  # noqa: E501
    escritor_csv = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';')
    escritor_csv.writeheader()

    for fila in data_dict_list_new:
        escritor_csv.writerow(fila)
