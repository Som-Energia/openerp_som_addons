# -*- coding: utf-8 -*-
{
    "name": "Funcions de suport a bateria virtual comer per SOM",
    "description": """
    This module provide :
        * Validació propia a giscedata_facturacio_bateria_virtual
    """,
    "version": "0-dev",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends":[
        "giscedata_facturacio_bateria_virtual",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "giscedata_bateria_virtual.xml",
        "giscedata_bateria_virtual_origen.xml",
    ],
    "active": False,
    "installable": True
}
