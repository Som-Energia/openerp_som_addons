# -*- coding: utf-8 -*-
{
    "name": "Vistes personalitzades de Som Energia",
    "description": """Vistes personalitzades de Som Energia""",
    "version": "0-dev",
    "author": "Som Energia",
    "category": "Generic Modules",
    "depends": [
        "base_extended_som",
        "som_autoreclama",
        "som_facturacio_comer",
    ],
    "init_xml": [],
    "demo_xml": [
    ],
    "update_xml": [
        "res_partner_view.xml",
        "giscedata_polissa_view.xml",
    ],
    "active": False,
    "installable": True,
}
