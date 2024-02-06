# -*- coding: utf-8 -*-
{
    "name": "Generació urbana",
    "description": "Mòdul per gestionar els grups de generació urbana",
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "crm_configuration",
        "giscedata_polissa",
        "giscedata_telemesures_base",
    ],
    "init_xml": [],
    "demo_xml": [
    ],
    "update_xml": [
        "som_gurb_data.xml",
        "som_gurb_cups_view.xml",
        "som_gurb_view.xml",
    ],
    "active": False,
    "installable": True,
}
