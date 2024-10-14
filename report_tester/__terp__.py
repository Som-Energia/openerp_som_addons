# -*- coding: utf-8 -*-
{
    "name": "report tester",
    "description": """
    This module provide :
        * menus models u wizards per poder testejar reports de manera integrada dins del erp
    """,
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": [
        "base",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "views/report_test_view.xml",
        "views/report_test_group_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
