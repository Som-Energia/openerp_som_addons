# -*- coding: utf-8 -*-
{
    "name": "som_atc",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
    * Funcionalitats sobre casos d'atencio al client
    """,
    "version": "0-dev",
    "author": "GISCE",
    "category": "Master",
    "depends": [
        "giscedata_atc_switching",
        "giscedata_atc_electricitat",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "res_partner_data.xml",
        "wizard/wizard_create_atc_from_polissa_view.xml",
        "views/giscedata_atc_view.xml",
    ],
    "active": False,
    "installable": True,
}
