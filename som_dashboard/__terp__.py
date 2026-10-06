# -*- coding: utf-8 -*-
{
    "name": "Dashboards personalitzats de SOM",
    "description": """
    """,
    "version": "0-dev",
    "author": "SOM Energia - ERP Team",
    "category": "Dashboards",
    "depends": ["board", "giscedata_polissa", "som_indexada"],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "som_dashboard_custom_search.xml",
        "som_dashboard_contractes.xml",
        "som_dashboard_gc_fase_3.xml",
        "som_dashboard_gc_tasca_1.xml",
        "som_dashboard_gc_endarrerits.xml",
    ],
    "active": False,
    "installable": True,
}
