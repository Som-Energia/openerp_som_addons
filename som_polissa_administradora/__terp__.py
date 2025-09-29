# -*- coding: utf-8 -*-
{
    "name": "Administradora d'una Pòlissa",
    "description": """
    This module provide :
        * Camp d'administradora per relacionar un contracte amb una administradora.
    """,
    "version": "24.5.0",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "l10n_ES_partner",
        "giscedata_polissa",
        "som_partner_account",
        "poweremail",
    ],
    "init_xml": [],
    "demo_xml": [
        "som_admin_notification_demo.xml",
    ],
    "update_xml": [
        "giscedata_polissa_view.xml",
        "res_partner_view.xml",
        "res_partner_data.xml",
        "wizard/wizard_modify_ov_admin_view.xml",
        "security/ir.model.access.csv",
        "som_polissa_administradora_data.xml",
        "som_administradora_notification_view.xml",
        "wizard/wizard_notify_ov_admin_view.xml",
    ],
    "active": False,
    "installable": True,
}
