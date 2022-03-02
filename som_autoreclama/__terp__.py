# -*- coding: utf-8 -*-
{
    "name": "Automatització de reclamacions",
    "description": """
    This module provide :
        * Model d'automatitzacio
        * Model d'historització
        * Vistes associades
    """,
    "version": "2.103.13",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends":[
        "base",
        "giscedata_atc_switching",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "som_autoreclama_pending_state_data.xml",
        "som_autoreclama_pending_state_view.xml",
    ],
    "active": False,
    "installable": True
}
