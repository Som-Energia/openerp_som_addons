# -*- coding: utf-8 -*-
{
    "name": "Adaptació Energética per Som Energia",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
  * Menú Energética
""",
    "version": "2.103.13",
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
        "som_energetica_view.xml",
        "som_energetica_data.xml",
        "giscedata_facturacio_data.xml",
    ],
    "active": False,
    "installable": True,
}
