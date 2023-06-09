# -*- coding: utf-8 -*-
{
    "name": "Giscedata Facturació Factura (SomEnergia)",
    "description": """Este módulo añade las siguientes funcionalidades:
    * Extiende giscedata_facturacio""",
    "version": "2.103.13",
    "author": "SomEnergia",
    "category": "GISCE extend",
    "depends": [
        "giscedata_facturacio",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "wizard/wizard_fraccionar_via_extralines_view.xml",
        "wizard/wizard_model_list_from_file_data.xml",
        "giscedata_facturacio_data.xml",
    ],
    "active": False,
    "installable": True,
}
