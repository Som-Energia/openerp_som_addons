# -*- coding: utf-8 -*-
# SCRIPT EN PYTHON 3
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import dbconfig
from erppeek import Client
from tqdm import tqdm
import os
import base64
import fitz

cups_erronis = []


def buscar_texto_en_pdf(pdf_path, texto_a_buscar):
    # Abre el archivo PDF
    documento = fitz.open(pdf_path)
    numero_paginas = documento.page_count

    # Itera sobre cada página del PDF
    for pagina_num in range(numero_paginas):
        pagina = documento.load_page(pagina_num)
        texto_pagina = pagina.get_text("text")

        # Busca el texto en la página actual
        if texto_a_buscar in texto_pagina:
            print('Texto encontrado en la página {pagina_num + 1}')
            return True

    return False


def eliminar_carpeta_si_esta_vacia(carpeta):
    try:
        os.rmdir(carpeta)
    except OSError:
        print('No se puede eliminar la carpeta "{carpeta}". Motivo: {e.strerror}')


conn = Client(**dbconfig.erppeek)

# Buscar CUPS de Catalunya i obtenir contractes actius on data baixa < 0/06/2021
cups_ids = conn.GiscedataCupsPs.search(
    [('id_provincia', 'in', [20, 28, 45, 9])], context={'active_test': False})

mail_no_trobat = []
adjunt_no_trobat = []
for cups_id in tqdm(cups_ids):
    try:
        cups_name = conn.GiscedataCupsPs.read(cups_id, ['name'])['name']
        carpeta = '/mnt/nfs/factures/{}'.format(cups_name)
        os.makedirs(carpeta)
        pol_ids = conn.GiscedataPolissa.search(
            [('cups', '=', cups_id)], context={'active_test': False})
        for pol_id in pol_ids:
            fac_ids = conn.GiscedataFacturacioFactura.search(
                [('polissa_id', '=', pol_id), ('data_inici', '>', '2021-06-01'),
                 ('type', '=', 'out_invoice')])
            numbers = conn.GiscedataFacturacioFactura.read(fac_ids, ['number']) or []
            for number in numbers:
                try:
                    mail_id = conn.PoweremailMailbox.search(
                        [('pem_subject', '=', 'Factura {}'.format(number['number']))])[0]
                except Exception as e:
                    mail_no_trobat.append(number['number'])
                try:
                    att_id = conn.IrAttachment.search(
                        [('res_id', '=', mail_id), ('res_model', '=', 'poweremail.mailbox')])
                    thatString = conn.IrAttachment.read(att_id[0], ['datas_mongo'])['datas_mongo']
                except Exception as e:
                    adjunt_no_trobat.append(number['number'])
                fitxer = os.path.join(carpeta, "{}.pdf".format(number['number']))
                with open(fitxer, "wb") as file:
                    file.write(base64.b64decode(thatString))
                if buscar_texto_en_pdf(fitxer, 'calculada'):
                    continue
                else:
                    os.remove(fitxer)
    except Exception as e:
        cups_erronis.append(cups_id)

    eliminar_carpeta_si_esta_vacia(carpeta)

print("CUPS erronis: {}".format(cups_erronis))
print("Mails no trobats: {}".format(mail_no_trobat))
print("Adjunt no trobats: {}".format(adjunt_no_trobat))
