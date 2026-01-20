# -*- coding: utf-8 -*-
{
    "name": "Gestió de comunicacions de sortida a contractres sense sòcia",
    "description": """Aquest mòdul gestiona les comunicacions de sortida a contractres
      que no són sòcies de Som Energia.
    """,
    "version": "0-dev",
    "author": "Som Energia SCCL",
    "category": "SomEnergia",
    "depends": [
        "som_account_invoice_pending",
        "som_polissa_soci",
        "som_switching",
    ],
    "init_xml": [],
    "demo_xml": [
        "demo/som_sortida_demo.xml",
    ],
    "update_xml": [
        "data/som_sortida_data.xml",
        "views/som_sortida_state_view.xml",
        "views/giscedata_polissa_view.xml",
        "views/som_sortida_history_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
