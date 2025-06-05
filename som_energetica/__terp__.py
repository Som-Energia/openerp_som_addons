# -*- coding: utf-8 -*-
{
    "name": "Adaptació Energética per Som Energia",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
  * Menú Energética
""",
    "version": "24.5.0",
    "author": "GISCE",
    "category": "Master",
    "depends": [
        "base",
        "giscedata_facturacio_comer",
        "som_polissa_soci",
        "som_switching",
        "som_polissa_administradora",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "views/som_energetica_view.xml",
        "data/som_energetica_data.xml",
        "data/giscedata_facturacio_data.xml",
    ],
    "active": False,
    "installable": True,
}
