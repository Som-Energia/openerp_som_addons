# -*- coding: utf-8 -*-
{
    "name": "Mòdul inforenergia de Som Energia'",
    "description": """
    This module provide :
        * Model enviament
        * Model lot enviament
        * Acció d'enviament
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends":[
        "base",
        "giscedata_polissa",
        "giscedata_facturacio",
        "poweremail_references",
    ],
    "init_xml": [],
    "demo_xml": [
        "tests/som_infoenergia_demo.xml"
    ],
    "update_xml":[
        "som_infoenergia_data.xml",
        "som_infoenergia_view.xml",
        "giscedata_polissa_view.xml",
        "security/infoenergia_security.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_download_pdf_view.xml",
        "wizard/wizard_download_csv_view.xml",
        "wizard/wizard_send_reports_view.xml",
    ],
    "active": False,
    "installable": True
}
