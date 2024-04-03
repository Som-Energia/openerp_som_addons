#-*- coding: utf-8 -*-
{
    "name": "Generació urbana",
    "description": "Mòdul per gestionar els grups de generació urbana",
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "giscedata_polissa",
        "giscedata_telemesures_base",
        "giscedata_facturacio_services",
        "giscedata_polissa_category",
        "giscedata_switching",
    ],
    "demo_xml": [
        "demo/som_gurb_service_demo.xml",
        "demo/som_gurb_demo.xml",
        "demo/som_gurb_cups_demo.xml",
    ],
    "update_xml": [
        "data/som_gurb_data.xml",
        "views/som_gurb_cups_view.xml",
        "views/som_gurb_view.xml",
        "views/som_gurb_webview.xml",
        "workflow/som_gurb_workflow.xml",
        "security/ir.model.access.csv",
    ],
    "init_xml": [],
    "active": False,
    "installable": True,
}
