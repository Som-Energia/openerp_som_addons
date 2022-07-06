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
        "poweremail_references",
        "som_polissa_soci",
        "som_generationkwh",
    ],
    "init_xml": [],
    "demo_xml": [
        "tests/som_infoenergia_demo.xml"
    ],
    "update_xml":[
        "som_infoenergia_report.xml",
        "som_infoenergia_sepa.xml",
        "som_infoenergia_data.xml",
        "som_infoenergia_view.xml",
        "giscedata_polissa_view.xml",
        "security/infoenergia_security.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_download_pdf_view.xml",
        "wizard/wizard_download_csv_view.xml",
        "wizard/wizard_send_reports_view.xml",
        "wizard/wizard_create_enviaments_from_object_view.xml",
        "wizard/wizard_multiple_state_change_view.xml",
        "wizard/wizard_add_contracts_lot_view.xml",
        "wizard/wizard_cancel_from_csv_view.xml",
        "wizard/wizard_create_enviaments_from_csv_view.xml",
        "wizard/wizard_create_enviaments_from_partner_view.xml",
    ],
    "active": False,
    "installable": True
}
