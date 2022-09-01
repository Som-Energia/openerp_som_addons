# -*- coding: utf-8 -*-
{
    "name": "Somenergia CRM lead",
    "description": """Crea el model CRM Lead per gestionar processos d'altes. 
    Aquest model exten el CRM afegint tots els camps necessaris per gestionar processos d'altes.
    Crea la seccio de CRM "Altes de socies".
    Afegeix un assistent per crear un nou soci a partir d'un CRM lead.
    Defineix els stages necessaris per els prcessos d'alta
    """,
    "version": "0-dev",
    "author": "Somenergia",
    "category": "GISCEMaster",
    "depends": [
        "crm_case_stage",
        "base_extended",
        "account_payment",
        "som_generationkwh",
    ],
    "init_xml": [],
    "demo_xml": [
    ],
    "update_xml": [
        "som_leads_data.xml",
        "security/ir.model.access.csv",
        "views/som_leads_view.xml",
    ],
    "active": False,
    "installable": True
}
