# -*- coding: utf-8 -*-
{
    "name": "Mòdul per crear informes per Consum",
    "description": """
    """,
    "version": "24.5.0",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "base",
        "c2c_webkit_report",
        "crm",
        "giscedata_polissa_comer",
        "giscedata_switching",
        "giscedata_facturacio_comer",
        "som_facturacio_switching",
    ],
    "init_xml": [],
    "demo_xml": [
        "tests/som_informe_demo.xml",
    ],
    "update_xml": [
        "data/som_informe_data.xml",
        "wizard/wizard_create_technical_report_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
