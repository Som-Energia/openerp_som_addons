# -*- coding: utf-8 -*-
{
    "name": "Mòdul per gestionar els canvis a facturació indexada",
    "description": """
    """,
    "version": "24.5.0",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "base",
        "base_extended_som",
        "giscedata_facturacio_indexada_som",
        "som_polissa",
        "giscedata_polissa",
        "giscedata_polissa_comer",
        "giscedata_polissa_category",
        "giscedata_lectures_pool",
        "giscedata_facturacio_iese",
        "giscedata_switching",
    ],
    "init_xml": [],
    "demo_xml": [
        "demo/product_pricelist_demo_data.xml",
        "demo/polissa_demo_data.xml",
    ],
    "update_xml": [
        "data/product_pricelist_periodes_data.xml",
        "data/product_pricelist_indexada_data.xml",
        "data/giscedata_polissa_category_data.xml",
        "data/email_template_data.xml",
        "data/res_config_data.xml",
        "wizard/wizard_change_to_indexada.xml",
        "wizard/wizard_massive_k_change.xml",
        "wizard/wizard_change_to_indexada_multi.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
