# -*- coding: utf-8 -*-
{
    "name": "backup de dades previ a eliminació",
    "description": """
    This module provide :
        * Model d'enmagatzemament temporal
        * Vistes associades
        * Scripts recurrents
    """,
    "version": "24.5.0",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends": [
        "base",
        "som_polissa",
        "som_switching",
        "som_generationkwh",
        "som_polissa_administradora",
    ],
    "init_xml": [
    ],
    "demo_xml": [],
    "update_xml": [
        "data/res_config_data.xml",
        "security/som_stash.xml",
        "security/ir.model.access.csv",
        "views/som_stash_view.xml",
        "views/som_stash_setting_view.xml",
        "wizard/wizard_som_stasher_view.xml",
        "wizard/wizard_som_unstasher_view.xml",
        "wizard/wizard_som_stash_this_view.xml",
    ],
    "active": False,
    "installable": True,
}
