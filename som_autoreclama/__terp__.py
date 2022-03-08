# -*- coding: utf-8 -*-
{
    "name": "Automatització de reclamacions",
    "description": """
    This module provide :
        * Model d'automatitzacio
        * Model d'historització
        * Vistes associades
    """,
    "version": "0-dev",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends":[
        "base",
        "giscedata_atc_switching",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "som_autoreclama_state_data.xml",
        "som_autoreclama_state_view.xml",
        "giscedata_atc_view.xml",
        "security/som_autoreclama.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True
}
