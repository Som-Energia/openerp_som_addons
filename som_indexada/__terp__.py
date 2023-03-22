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
        "giscedata_facturacio_iese",
        "giscedata_switching",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "wizard/wizard_change_to_indexada.xml",
        "data/product_pricelist_data.xml",
    ],
    "active": False,
    "installable": True
}