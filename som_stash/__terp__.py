# -*- coding: utf-8 -*-
{
    "name": "backup de dades previ a eliminació",
    "description": """
    This module provide :
        * Model d'enmagatzemament temporal
        * Vistes associades
        * Scripts recurrents 
    """,
    "version": "0-dev",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends": [
        "base",
    ],
    "init_xml": [        
    ],
    "demo_xml": [],
    "update_xml": [
        "security/som_stash.xml",
        "security/ir.model.access.csv",
        "views/som_stash_view.xml",
    ],
    "active": False,
    "installable": True,
}
