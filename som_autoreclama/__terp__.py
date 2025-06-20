# -*- coding: utf-8 -*-
{
    "name": "Automatització de reclamacions",
    "description": """
    This module provide :
        * Model d'automatitzacio
        * Model d'historització
        * Vistes associades
    """,
    "version": "24.5.0",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends": [
        "base",
        "giscedata_subtipus_reclamacio",
        "som_facturacio_switching",
        "som_switching",
        "som_polissa",
        "som_atc",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "som_autoreclama_state_data.xml",
        "som_autoreclama_state_view.xml",
        "wizard/wizard_som_autoreclama_execute_step_view.xml",
        "wizard/wizard_som_autoreclama_set_manual_state_view.xml",
        "wizard/wizard_som_autoreclama_generated_atc_view.xml",
        "wizard/wizard_som_autoreclama_set_disable_state_view.xml",
        "giscedata_atc_view.xml",
        "giscedata_polissa_view.xml",
        "security/som_autoreclama.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_massive_create_r1029_view.xml",
        "res_config_data.xml",
    ],
    "active": False,
    "installable": True,
}
