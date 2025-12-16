# -*- coding: utf-8 -*-
{
    "name": "Base extension de Som Energia",
    "description": """Base models extensions""",
    "version": "24.5.0",
    "author": "Som Energia",
    "category": "Generic Modules",
    "depends": [
        "base_extended",
        "poweremail",
    ],
    "init_xml": [],
    "demo_xml": [
        "demo/poweremail_demo_data.xml",
    ],
    "update_xml": [
        "data/res_users_data.xml",
        "data/res_request_link_data.xml",
        "data/base_extended_som_data.xml",
        "data/res_phone_national_code_data.xml",
        "views/res_partner_view.xml",
        "views/res_partner_address_view.xml",
        "views/res_phone_national_code_view.xml",
        "views/poweremail_sendgrid_category_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
