from erppeek import Client
import dbconfig;

"""_summary_
Executa tots les tasques actives de som_crawlers sobrescrivint el 'days_of_margin' (tasques d'importació)
"""

DAYS_OF_MARGIN = 15

O = Client(**dbconfig.erppeek)

active_ids = O.SomCrawlersTask.search() # TODO: Just imports, not exports
wiz = O.WizardExecutarTasca.create({})
wiz.executar_tasca(context={'active_ids': active_ids, 'days_of_margin': DAYS_OF_MARGIN})