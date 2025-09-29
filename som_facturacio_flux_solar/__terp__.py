# -*- coding: utf-8 -*-
{
    "name": "Funcions de suport a bateria virtual comer per SOM",
    "description": """
    This module provide :
        * Validació propia a giscedata_facturacio_bateria_virtual
    """,
    "version": "24.5.0",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "giscedata_facturacio_bateria_virtual",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "security/ir.model.access.csv",
        "giscedata_bateria_virtual.xml",
        "giscedata_bateria_virtual_origen.xml",
        "giscedata_bateria_virtual_percentatges_acumulacio_data.xml",
    ],
    "active": False,
    "installable": True,
}
