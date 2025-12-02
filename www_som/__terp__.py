# -*- coding: utf-8 -*-
{
    "name": "Integració WWW",
    "description": """
Mòdul per la integració de l'oficina virtual
    """,
    "version": "24.5.0",
    "author": "GISCE-TI, S.L.",
    "category": "www",
    "depends": [
        "base_extended",
        "base_extended_som",
        "www_base",
        "som_polissa_soci",
        "som_indexada",
        "som_infoenergia",
        "poweremail",
        "giscedata_lectures_comer",
        "giscedata_lectures_pool",
        "giscedata_facturacio_impagat_comer",
        "giscedata_atc_switching",
        "som_account_invoice_pending",
    ],
    "init_xml": [],
    "demo_xml": [
        "demo/res_partner_demo.xml",
        "demo/indexed_prices_demo.xml",
        "demo/ov_attachment_demo.xml",
    ],
    "update_xml": [
        "www_som_data.xml",
        "wizard/wizard_model_list_from_file_data.xml",
        "security/ir.model.access.csv",
        "ir_attachment_view.xml",
        "data/pricelist_social_data.xml",
    ],
    "active": False,
    "installable": True,
}
