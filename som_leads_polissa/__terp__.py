# -*- coding: utf-8 -*-
{
    "name": "som_leads_polissa",
    "description": """
    This module provide :
        * Afegir o modificar funcionalitats dels leads base
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends":[
        "base_bank_extended",
        "giscedata_crm_leads",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        'giscedata_crm_lead_view.xml'
    ],
    "active": False,
    "installable": True
}
