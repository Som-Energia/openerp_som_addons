# -*- coding: utf-8 -*-
{
    "name": "Account invoice comer (SomEnergia)",
    "description": """Este módulo añade las siguientes funcionalidades:
    * Extiende account_invoice""",
    "version": "24.5.0",
    "author": "GISCE",
    "category": "GISCEMaster",
    "depends": [
        "account_invoice_base",
        "account_payment_extension",
        "poweremail",
        "giscedata_remeses",
        "l10n_ES_remesas",
        "som_polissa_soci",
    ],
    "init_xml": [],
    "demo_xml": [
        "tests/account_invoice_demo.xml",
    ],
    "update_xml": [
        "account_invoice_som_report.xml",
        "account_invoice_view.xml",
        "account_invoice_data.xml",
        "wizard/wizard_payment_order_add_invoices_view.xml",
        "wizard/wizard_export_remesas_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
