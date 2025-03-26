# -*- coding: utf-8 -*-
{
    "name": "Mòdul de comptes",
    "description": """
    This module provide :
        * Obligació que un compte comptable tingui pare
    """,
    "version": "24.5.0",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "account",
        "account_financial_report",
        "async_reports",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "account_view.xml",
        "wizard/wizard_account_balance_report_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
