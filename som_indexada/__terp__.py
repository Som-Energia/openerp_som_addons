# -*- coding: utf-8 -*-
{
    "name": "Mòdul per gestionar els canvis a facturació indexada",
    "description": """
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends":[
        "base",
        "giscedata_facturacio_indexada_som",
        "giscedata_polissa",
        "giscedata_polissa_comer",
        "giscedata_lectures_pool",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "wizard/wizard_change_to_indexada.xml"
    ],
    "active": False,
    "installable": True
}