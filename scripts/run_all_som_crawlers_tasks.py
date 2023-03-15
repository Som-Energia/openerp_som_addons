from erppeek import Client
import dbconfig

"""_summary_
Executa tots les tasques actives de som_crawlers sobrescrivint el
'days_of_margin' (tasques d'importació)
"""

client = Client(**dbconfig.erppeek)

active_ids = client.SomCrawlersTask.search()  # TODO: Just imports, not exports
wiz = client.WizardExecutarTasca.create({})
wiz.executar_tasca(context={"active_ids": active_ids})
