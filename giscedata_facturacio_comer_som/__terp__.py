# -*- coding: utf-8 -*-
{
    "name": "Reports Facturació SOM (Comercialitzadora)",
    "description": """Reports Facturació SOM (Comercialitzadora)""",
    "version": "0-dev",
    "author": "GISCE",
    "category": "Extrareports",
    "depends":[
        'base',
        'c2c_webkit_report',
        "account_invoice_base",
        "giscedata_facturacio_comer",
        "giscedata_polissa_comer",
        "som_polissa_soci",
        "jasper_reports",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "giscedata_facturacio_comer_data.xml",
        "giscedata_facturacio_comer_report.xml"
    ],
    "active": False,
    "installable": True
}
