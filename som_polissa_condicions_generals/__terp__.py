# -*- coding: utf-8 -*-
{
    "name": "Condicions generals Somenergia",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
    * Condicions generals pòlisses Somenergia
    """,
    "version": "2.107.5",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "giscedata_polissa",
        "giscedata_facturacio_comer",
        "giscedata_polissa_condicions_generals",
        "giscedata_facturacio_indexada_som",
        "som_leads_polissa",
        "report_puppeteer",
        "giscedata_facturacio_iese",
    ],
    "init_xml": [],
    "demo_xml": ["demo/res_partner_demo.xml"],
    "update_xml": [
        "data/giscedata_polissa_condicions_generals_data.xml",
        "data/giscedata_switching_data_m1.xml",
        "report/giscedata_polissa_condicions_generals_report.xml",
        "report/giscedata_polissa_condicions_generals_m101_report.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
