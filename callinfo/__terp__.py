# -*- coding: utf-8 -*-
{
    "name": "Suport a app callinfo",
    "description": """
    This module provide :
        * Model enmagatzemament
        * Vistes associades
    """,
    "version": "0-dev",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends":[
        "base",
        "som_autoreclama",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "call_info_call_log_view.xml",
        "call_info_call_category_view.xml",
        "call_info_call_category_data.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True
}
