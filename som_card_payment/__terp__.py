# -*- coding: utf-8 -*-
{
    "name": "Pagament per targeta de Som Energia",
    "description": """Mòdul per gestionar el pagament per targeta de Som Energia""",
    "version": "0-dev",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends": ["base", "account", "account_payment"],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "security/ir.model.access.csv",
        "data/payment_type_data.xml",
        "views/res_partner_creditcard_view.xml",
        "views/res_partner_view.xml",
    ],
    "active": False,
    "installable": True,
}
