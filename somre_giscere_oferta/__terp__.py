# -*- coding: utf-8 -*-
{
    "name": "GISCE RE Oferta Som Energia",
    "description": """Mòdul de generació i publicació d'Ofertas de Generació""",
    "version": "0-dev",
    "author": "GISCE",
    "category": "RE",
    "depends": [
        "giscere_omie",
    ],
    "init_xml": [],
    "demo_xml": [

    ],
    "update_xml": [
        "giscere_oferta_scheduler.xml",
        "somre_giscere_oferta_template.xml"
    ],
    "active": False,
    "installable": True
}