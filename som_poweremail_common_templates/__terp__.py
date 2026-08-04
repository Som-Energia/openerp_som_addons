# -*- coding: utf-8 -*-
{
    "name": "Som Poweremail Common Templates",
    "description": """
    This module provide:
        * Common templates to be used in the rest of poweremail templates,
    p.e. header with customer data, logo, footer, legal texts... etc.
    """,
    "version": "0-dev",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends": [
        "base",
        "poweremail",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "commontemplates_data.xml",
        "poweremail_send_mail_view.xml",
        "generic_templates_data.xml",
    ],
    "active": False,
    "installable": True,
}
