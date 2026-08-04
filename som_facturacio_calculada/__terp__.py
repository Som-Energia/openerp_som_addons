# -*- coding: utf-8 -*-
{
    "name": "Mòdul per crear lectures calculades per a la facturació",
    "description": """
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "som_facturacio_comer",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "som_facturacio_calculada_data.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_crear_lectures_calculades_view.xml",
    ],
    "active": False,
    "installable": True,
}
