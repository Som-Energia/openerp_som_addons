# -*- coding: utf-8 -*-
{
    "name": "som_switching2",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
  * Categories per les pòlisses per els casos de switching
""",
    "version": "0-dev",
    "author": "GISCE",
    "category": "Master",
    "depends":[
        "giscedata_switching",
        "giscedata_facturacio_switching",
        "som_polissa_soci",
        "giscedata_polissa_category",
        "giscedata_polissa_responsable",
        "giscedata_facturacio_suspesa",
        "giscedata_atc_switching"
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'giscedata_switching_data.xml',
    ],
    "active": False,
    "installable": True
}