# -*- coding: utf-8 -*-
{
    "name": "som_estalvi",
    "description": """
        Funcions i continguts per millorar l'estalvi dels contractes de SOM
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "report_puppeteer",
        "som_polissa",
        "som_assets",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "security/ir.model.access.csv",
        "wizard/wizard_contract_power_optimization_view.xml",
        "report/som_estalvi_report.xml",
    ],
    "active": False,
    "installable": True,
}
