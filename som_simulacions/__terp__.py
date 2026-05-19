# -*- coding: utf-8 -*-
{
    "name": "som_simulacions",
    "description": "Mòdul base per simulacions",
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": ["base"],
    "init_xml": [],
    "demo_xml": [
        "demo/annual_coeff_demo.xml",
        "demo/energy_price_demo.xml",
        "demo/simulation_request_demo.xml",
    ],
    "update_xml": [
        "security/som_simulacions_security.xml",
        "security/ir.model.access.csv",
        "views/parameter_views.xml",
        "views/simulation_views.xml",
        "views/menu.xml",
    ],
    "active": False,
    "installable": True,
}
