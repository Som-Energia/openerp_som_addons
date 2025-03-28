# -*- coding: utf-8 -*-
{
    "name": "som_switching",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
  * Categories per les pòlisses per els casos de switching
""",
    "version": "24.5.0",
    "author": "GISCE",
    "category": "Master",
    "depends": [
        "giscedata_switching",
        "giscedata_facturacio_switching",
        "som_polissa_soci",
        "giscedata_polissa_category",
        "giscedata_polissa_responsable",
        "giscedata_facturacio_suspesa",
        "giscedata_atc_switching",
        "giscedata_switching_multi_close",
        "giscedata_switching_comer",
    ],
    "init_xml": [],
    "demo_xml": [
        "demo/som_switching_demo_data.xml",
    ],
    "update_xml": [
        "giscedata_switching_view.xml",
        "giscedata_switching_data.xml",
        "wizard/wizard_create_r1_from_multiple_contracts_view.xml",
        "wizard/giscedata_switching_wizard_r1_invoice.xml",
        "wizard/wizard_a3_from_contract_view.xml",
        "wizard/giscedata_switching_mod_con_wizard_view.xml",
        "wizard/wizard_generate_R1_from_F1_erroni.xml",
        "giscedata_atc_data.xml",
        "giscedata_switching_activation_data.xml",
        "giscedata_facturacio_switching_error_data.xml",
        "wizard/wizard_comment_to_F1_view.xml",
        "wizard/wizard_validate_d101_view.xml",
        "security/ir.model.access.csv",
        "giscedata_switching_rebutjos_m.xml",
        "giscedata_switching_rebutjos_c.xml",
        "giscedata_switching_rebutjos_a.xml",
        "giscedata_polissa_view.xml",
        "giscedata_switching_notification_data.xml",
        "wizard/wizard_create_atc_from_polissa.xml",
        "giscedata_atc_view.xml",
        "wizard/giscedata_switching_wizard_b1.xml",
        "wizard/wizard_close_obsolete_cases.xml",
        "wizard/giscedata_switching_log_reexport_wizard_view.xml",
    ],
    "active": False,
    "installable": True,
}
