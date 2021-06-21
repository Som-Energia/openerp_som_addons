# -*- coding: utf-8 -*-
{
    "name": "Mòdul per crear informes per Consum",
    "description": """
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends":[
        "base",
        "giscedata_polissa",
        "giscedata_facturacio",
        "crm",
    ],
    "init_xml": [],
    "demo_xml": [
    ],
    "update_xml":[
        "data/som_informe_data.xml",
        "wizard/wizard_create_report_view.xml",
    ],
    "active": False,
    "installable": True
}
