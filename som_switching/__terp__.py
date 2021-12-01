# -*- coding: utf-8 -*-
{
    "name": "som_switching",
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
        "giscedata_atc_switching",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'giscedata_switching_view.xml',
        'giscedata_switching_data.xml',
        'wizard/wizard_create_r1_from_multiple_contracts_view.xml',
        'wizard/giscedata_switching_wizard_r1_invoice.xml',
        'wizard/wizard_a3_from_contract_view.xml',
        'wizard/giscedata_switching_mod_con_wizard_view.xml',
        'wizard/wizard_generate_R1_from_F1_erroni.xml',
        'giscedata_atc_data.xml',
        'giscedata_switching_activation_data.xml',
        'giscedata_facturacio_switching_error_data.xml',
        'wizard/wizard_comment_to_F1_view.xml',
        'security/ir.model.access.csv',
        'giscedata_switching_rebuitjos_c.xml',
        'giscedata_switching_rebuitjos_a.xml',
    ],
    "active": False,
    "installable": True
}
