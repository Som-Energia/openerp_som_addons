{
    "name": "Mòdul per descarregar fitxers distribuidores electricitat",
    "description": """ """,
    "version": "24.5.0",
    "author": "SomEnergia",
    "category": "Master",
    "depends": [
        "base",
        "giscedata_switching",
        "giscedata_facturacio_switching",
        "oorq",
    ],
    "init_xml": [],
    "demo_xml": [
        "demo/som_crawlers_demo.xml",
    ],
    "update_xml": [
        "data/som_crawlers_config_data.xml",
        "data/som_crawlers_task_data.xml",
        "data/som_crawlers_step_data.xml",
        "views/som_crawlers_config_view.xml",
        "views/som_crawlers_task_step_view.xml",
        "views/som_crawlers_task_view.xml",
        "views/som_crawlers_result_view.xml",
        "views/som_crawlers_holiday_view.xml",
        "wizard/wizard_executar_tasca.xml",
        "wizard/wizard_canviar_dies_de_marge.xml",
        "wizard/wizard_canviar_usuari.xml",
        "wizard/wizard_canviar_contrasenya.xml",
        "wizard/wizard_change_field_value.xml",
        "security/crawlers_security.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
