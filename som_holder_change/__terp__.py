# -*- coding: utf-8 -*-
{
    "name": "Som Energia Holder Change",
    "description": """
    Holder change request management for existing contracts.
    """,
    "version": "0.1",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "som_polissa",
        "som_switching",
        "som_polissa_condicions_generals",
        "giscedata_signatura_documents_signaturit",
        "som_card_payment",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
