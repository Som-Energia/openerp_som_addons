# -*- coding: utf-8 -*-
{
    "name": "som_leads_polissa",
    "description": """
    This module provide :
        * Afegir o modificar funcionalitats dels leads base
    """,
    "version": "24.5.0",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "base_bank_extended",
        "giscedata_crm_leads",
        "giscedata_crm_importador",
        "som_polissa",
        "som_indexada",
        "som_partner_seq",
        "partner_representante",
    ],
    "init_xml": [],
    "demo_xml": [
        "demo/res_partner_demo.xml"
    ],
    "update_xml": [
        "giscedata_crm_lead_view.xml",
        "data/giscedata_crm_lead_data.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_crm_lead_create_entities_view.xml",
        "wizard/wizard_importador_leads_comercials_view.xml",
    ],
    "active": False,
    "installable": True,
}
