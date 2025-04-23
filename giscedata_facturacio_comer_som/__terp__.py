# -*- coding: utf-8 -*-
{
    "name": "Reports Facturació SOM (Comercialitzadora)",
    "description": """Reports Facturació SOM (Comercialitzadora)""",
    "version": "24.5.0",
    "author": "GISCE",
    "category": "Extrareports",
    "depends": [
        "base",
        "c2c_webkit_report",
        "account_invoice_base",
        "giscedata_facturacio_comer",
        "giscedata_sup_territorials_2013_tec271_comer",
        "giscedata_facturacio_iese",
        "giscedata_polissa_comer",
        "som_polissa_soci",
        "jasper_reports",
        # "giscedata_omie_comer",
    ],
    "init_xml": [],
    "demo_xml": ["giscedata_facturacio_comer_som_demo.xml"],
    "update_xml": [
        "giscedata_facturacio_comer_data.xml",
        "giscedata_facturacio_comer_report.xml",
        "giscedata_facturacio_factura.xml"
    ],
    "active": False,
    "installable": True,
}
