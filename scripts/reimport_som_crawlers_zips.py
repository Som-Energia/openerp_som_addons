# -*- coding: utf-8 -*-
from datetime import datetime
import dbconfig
from erppeek import Client

"""_summary_
Reimporta fitxers ZIPs trobats en Resultats de som_crawlers que han acabat amb Failed
Aquest script s'ha d'executar després de la pimera onada de crawlers (7 hores)
"""

O = Client(**dbconfig.erppeek)  # noqa: E741


# Obtenir la llista de resultats a tractar
craw_ids = O.SomCrawlersTask.search([("resultat_bool", "=", False)])

total_crawlers = 0
total_reintents = 0
total_correctes = 0

for craw_id in craw_ids:
    attachment = []
    craw = O.SomCrawlersTask.browse(craw_id)
    if craw.run_ids:
        last_result = craw.run_ids[0]
        attachment_ids = O.IrAttachment.search(
            [
                ("res_id", "=", last_result.id),
                ("name", "ilike", ".zip"),
            ]
        )
        if not attachment_ids:
            continue
        total_crawlers += 1
        total_reintents += len(attachment_ids)
        # Reimportar xml
        result = True
        output = "[{} REIMPORTACIONS]:\n\n".format(total_reintents)
        for attachment_id in attachment_ids:
            attachment = O.IrAttachment.browse(attachment_id)
            try:
                output += craw.task_step_ids[-1].import_wizard(attachment.name, attachment.datas)
            except Exception as e:
                output += "Error carregant el fitxer {}: {} \n".format(attachment.name, str(e))
                result = False
            else:
                total_correctes += 1

        output += "\n{} reimportats correctament".format(total_correctes)
        # Afegir nou resultat al crawler
        O.SomCrawlersResult.create(
            {
                "task_id": craw_id,
                "data_i_hora_execucio": datetime.now().strftime("%Y-%m-%d_%H:%M"),
                "resultat_bool": result,
                "resultat_text": output,
            }
        )

print """
    Hem trobat {} crawlers per reimportar.
     S'han intentat reimportat {} fitxers.
     S'han reimportat correctament {} fitxers.""".format(   # noqa: E999
    total_crawlers, total_reintents, total_correctes
)
