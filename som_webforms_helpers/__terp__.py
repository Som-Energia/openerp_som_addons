# -*- coding: utf-8 -*-
{
    "name": "Webforms Helpers for Som Energia",
    "description": """Aquest mòdul afegeix funcions per donar suport a l'API de Webforms""",
    "version": "2.103.13",
    "author": "SOMEnergia",
    "category": "Master",
    "depends":[
        "base",
        "giscedata_facturacio_comer",
        "som_facturacio_switching",
        "som_generationkwh"
    ],
    "init_xml": [],
    "demo_xml": [
        "tests/tarifes_demo.xml",
    ],
    "update_xml":[
        "som_webforms_helpers_data.xml"
    ],
    "active": False,
    "installable": True
}
