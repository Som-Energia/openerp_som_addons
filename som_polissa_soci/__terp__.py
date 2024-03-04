# -*- coding: utf-8 -*-
{
    "name": "Soci d'una Pòlissa",
    "description": """
    This module provide :
        * Camp de soci per relacionar un contracte amb un soci.
    """,
    "version": "0-dev",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "giscedata_facturacio_comer",
        "giscedata_lectures_estimacio",
        "giscedata_polissa_category",
    ],
    "init_xml": ["res_partner_data.xml"],
    "demo_xml": ["res_partner_demo_data.xml"],
    "update_xml": [
        "giscedata_polissa_view.xml",
        "giscedata_facturacio_data.xml",
        "giscedata_polissa_category_data.xml",
        "res_partner_view.xml",
        "somenergia_soci_view.xml",
        "giscedata_facturacio_view.xml",
        "wizard/wizard_update_invoice_check_ov_visible_view.xml",
        "security/ir.model.access.csv",
        "giscedata_som_soci_data.xml",
        "wizard/wizard_subscribe_client_mailchimp.xml",
        "wizard/wizard_subscribe_soci_mailchimp.xml",
        "wizard/wizard_unsubscribe_soci_mailchimp.xml",
    ],
    "active": False,
    "installable": True,
}
