# -*- coding: utf-8 -*-
{
    "name": "Account invoice comer (SomEnergia)",
    "description": """Este módulo añade las siguientes funcionalidades:
    * Extiende account_invoice""",
    "version": "2.103.13",
    "author": "GISCE",
    "category": "GISCEMaster",
    "depends":[
        "account_invoice_base",
        "poweremail",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "account_invoice_som_report.xml"
    ],
    "active": False,
    "installable": True
}
