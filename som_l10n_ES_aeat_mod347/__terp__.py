# -*- coding: utf-8 -*-
{
    "name": "Som AEAT 347",
    "description": """
    """,
    "version": "0-dev",
    "author": "Som",
    "category": "Master",
    "depends": ["base_extended_som", "account", "l10n_ES_aeat_mod347", "poweremail"],
    "init_xml": [],
    "demo_xml": [
        "demo/som_l10n_ES_aeat_mod347_demo.xml",
    ],
    "update_xml": [
        "wizard/wizard_send_email_over_limit.xml",
        "wizard/wizard_send_email_over_limit_to_partner.xml",
        "security/ir.model.access.csv",
        "som_l10n_ES_aeat_mod347_data.xml",
    ],
    "active": False,
    "installable": True,
}
