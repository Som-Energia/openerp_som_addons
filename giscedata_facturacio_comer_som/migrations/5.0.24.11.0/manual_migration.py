# coding=utf-8
from erppeek import Client
import dbconfig
from tqdm import tqdm
from consolemsg import step, success
import csv
import StringIO

"""_summary_
Executa la migració un cop creat el camp enviat_mail_id a giscedata_facturacio_factura pot trigar mes de 24 h
"""  # noqa: E501

O = Client(**dbconfig.erppeek)  # noqa: E741

mail_obj = O.PoweremailMailbox
fact_obj = O.GiscedataFacturacioFactura


DOIT = False

not_found_ab_invoices = []
not_found_fe_invoices = []
not_found_xx_invoices = []
subjects = [
    u'Factura XX',
    u'Som Energia: Factura XX',
    u'Factura electricitat XX',
    u'Factura electricidad XX',
    u'Abonament factura electricitat XX \\ Abono factura electricidad XX',
    u'Reenviament XX (adjunt correcte) / Reenvío XX (adjunto correcto)',
    u'Reenvío de factura XX',
    u'Reenviament Factura XX',
    u'Reenvío Factura XX',
    u'Factura complementària per expedient XX',
    u'Factura complementaria por expediente XX',
    u'Factura XX - Factura expedient distribuïdora',
    u'Factura XX - factura expedient distribuïdora',
    u'Factura XX - Factura expediente distribuidora',
    u'Factura XX - factura expediente distribuidora',
    u'Factura XX associada a expedient',
    u'Factura XX de expediente de la empresa distribuidora',
    u'Factura XX per expedient distribuïdora',
    u'Factura abonadora XX',
    u'Factura XX amb facturació complementària de la distribuïdora',
    u'Factura XX con expediente de la empresa distribuidora',
    u'Factura XX amb expedient distribuïdora',
    u'Factura XX amb expedient empresa distribuïdora',
    u'Factura XX amb lectures estimades per la distribuïdora',
    u'Factura XX - Import elevat',
    u'Facturación atrasada + Factura XX',
    u'Factura XX - diciembre',
    u'Factura XX amb estimacions reiterades de la distribuïdora',
    u'Factura XX con lectura estimada por la distribuidora',
    u'Factura XX amb lectura estimada per la distribuïdora',
    u'Factura XX amb lectures estimades de la distribuïdora',
    u'Factura XX amb estimacions de la ditribuïdora',
]


def get_fact_to_update():
    fact_ids = fact_obj.search([
        ('number', '!=', None),
        ('enviat', '=', True),
        ('enviat_carpeta', '=', 'sent'),
        ('type', 'in', ['out_invoice', 'out_refund']),
        ('enviat_mail_id', '=', None),
    ])
    return fact_ids


def search_email(fact_id, fact_number, sent_date):
    query = [
        ('folder', '=', 'sent'),
        ('reference', '=', 'giscedata.facturacio.factura,{}'.format(fact_id)),
        ('date_mail', '<=', sent_date),
    ]

    # Let's try the fastest ones
    for subject in subjects:
        full_subject = subject.replace("XX", fact_number)
        mail_ids = mail_obj.search(
            [('pem_subject', '=', full_subject)] + query
        )
        if mail_ids:
            return mail_ids

    if fact_number.startswith('AB'):
        not_found_ab_invoices.append(fact_id)
        step('Not found AB --> {}', fact_number)
    elif fact_number.startswith('FE'):
        not_found_fe_invoices.append(fact_id)
        success('Not found FE --> {}', fact_number)
    else:
        not_found_xx_invoices.append(fact_id)
        success('not found OTHER --> {}', fact_number)
    return mail_ids


def update_field(fact_id):
    fact_data = fact_obj.read(fact_id, ['number', 'enviat_data'])
    mail_ids = search_email(fact_id, fact_data['number'], fact_data['enviat_data'])
    if not mail_ids:
        return False

    if DOIT:
        fact_obj.write(fact_id, {'enviat_mail_id': mail_ids[0]})
    return True


def write_as_csv(header, data, filename):
    csv_doc = StringIO.StringIO()
    writer_report = csv.writer(csv_doc, delimiter=';')
    writer_report.writerow(header)
    writer_report.writerows(data)
    doc = csv_doc.getvalue()
    with open(filename + ".csv", 'w') as f:
        f.write(doc)


def write_as_csv_assist(fact_ids, filename):
    O = Client(**dbconfig.erppeek)  # noqa: E741
    f_obj = O.GiscedataFacturacioFactura

    header = ['id', 'numero', 'polissa', 'enviat', 'carpeta mail', 'data enviament']
    data = []
    for fact_id in fact_ids:
        val = f_obj.read(
            fact_id,
            [
                'number',
                'polissa_id',
                'enviat',
                'enviat_carpeta',
                'enviat_data'
            ]
        )
        data.append([
            val['id'],
            val['number'],
            val['polissa_id'][1],
            val['enviat'],
            val['enviat_carpeta'],
            val['enviat_data']
        ])
    write_as_csv(header, data, filename)


def migrate():
    found = 0
    not_found = 0
    step("Starting migration: reading the id's")
    fact_ids = get_fact_to_update()
    step("{} id's found...", len(fact_ids))
    for count, fact_id in enumerate(tqdm(fact_ids)):
        if update_field(fact_id):
            found += 1
        else:
            not_found += 1
        if count % 5000 == 0:
            step("Status found/not found {} / {}", found, not_found)
    step("Column succesfuly filled")
    step("Status found/not found {} / {}", found, not_found)
    write_as_csv_assist(not_found_ab_invoices, 'not_found_AB_inv')
    write_as_csv_assist(not_found_fe_invoices, 'not_found_FE_inv')
    write_as_csv_assist(not_found_xx_invoices, 'not_found_XX_inv')


if __name__ == '__main__':
    try:
        migrate()
    except (KeyboardInterrupt, SystemError):
        write_as_csv_assist(not_found_ab_invoices, 'not_found_AB_inv')
        write_as_csv_assist(not_found_fe_invoices, 'not_found_FE_inv')
        write_as_csv_assist(not_found_xx_invoices, 'not_found_XX_inv')
        success("Bye!")
