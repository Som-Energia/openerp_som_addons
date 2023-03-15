# -*- coding: utf-8 -*-
{
    "name": "Mòdul per crear un assitent per ajudar a la impresuió de factures en paper",
    "description": """
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "base",
        "giscedata_facturacio_comer",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "som_factures_paper.xml",
        "wizard/wizard_paper_invoice_som.xml",
        "security/ir.model.access.csv",
        "giscedata_polissa_view.xml",
    ],
    "active": False,
    "installable": True,
}
