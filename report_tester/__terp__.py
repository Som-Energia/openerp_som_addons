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
        "wizard/wizard_report_test_group_view_tests.xml",
        "wizard/wizard_report_test_group_accept_tests.xml",
        "wizard/wizard_report_test_group_execute_tests.xml",
        "wizard/wizard_report_test_accept_test.xml",
        "wizard/wizard_report_test_execute_test.xml",
        "views/report_test_view.xml",
        "views/report_test_group_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}