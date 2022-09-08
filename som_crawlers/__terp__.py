{
    "name": "Mòdul per descarregar fitxers distribuidores electricitat",
    "description": """ """,
    "version": "0.1",
    "author": "SomeEnergia",
    "category": "Master",
    "depends":[
        "base",
        "giscedata_switching",
        "giscedata_facturacio_switching",
        "oorq",
    ],
    "init_xml":[],
    "demo_xml": [
        "demo/som_crawlers_demo.xml",
    ],
    "update_xml":[
        "views/som_crawlers_config_view.xml",
        "views/som_crawlers_result_view.xml",
        "views/som_crawlers_task_step_view.xml",
        "views/som_crawlers_task_view.xml",
        "data/som_crawlers_data.xml",
        "views/som_crawlers_task_view.xml",
        "wizard/wizard_executar_tasca.xml",
        "wizard/wizard_canviar_dies_de_marge.xml",
    ],
    "active": False,
    "installable":True
}