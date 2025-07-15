# -*- coding: utf-8 -*-
{
    "name": "Gestió de comunicacions de sortida a contractres sense sòcia",
    "description": """Aquest mòdul gestiona les comunicacions de sortida a contractres
      que no són sòcies de Som Energia.
    """,
    "version": "24.5.0",
    "author": "Som Energia",
    "category": "Master",
    "depends": [
        "som_account_invoice_pending",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "data/som_sortida_data.xml",
        "views/som_sortida_state_view.xml",
        "views/giscedata_polissa_view.xml",
        "security/ir.model.access.csv"
    ],
    "active": False,
    "installable": True,
}
