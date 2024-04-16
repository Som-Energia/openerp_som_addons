# -*- coding: utf-8 -*-
{
    "name": "Integració WWW",
    "description": """
Mòdul per la integració de l'oficina virtual
    """,
    "version": "0-dev",
    "author": "GISCE-TI, S.L.",
    "category": "www",
    "depends": [
        "base_extended",
        "www_base",
        "som_polissa_soci",
        "som_indexada",
        "giscedata_lectures_comer",
        "giscedata_lectures_pool",
        "giscedata_facturacio_impagat_comer",
        "giscedata_atc_switching",
    ],
    "init_xml": [],
    "demo_xml": [
        "tests/res_partner_demo.xml",
        "tests/indexed_prices_demo.xml",
    ],
    "update_xml": [
        "www_som_data.xml",
        "res_partner_view.xml",
        "wizard/wizard_model_list_from_file_data.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
