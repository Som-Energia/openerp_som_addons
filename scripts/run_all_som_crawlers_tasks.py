from erppeek import Client
import dbconfig

"""_summary_
Executa tots les tasques actives de som_crawlers sobrescrivint el 'days_of_margin' (tasques d'importació)
"""  # noqa: E501

O = Client(**dbconfig.erppeek)  # noqa: E741

active_ids = O.SomCrawlersTask.search()  # TODO: Just imports, not exports
wiz = O.WizardExecutarTasca.create({})
wiz.executar_tasca(context={"active_ids": active_ids})
