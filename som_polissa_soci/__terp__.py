# -*- coding: utf-8 -*-
{
    "name": "Soci d'una Pòlissa",
    "description": """
    This module provide :
        * Camp de soci per relacionar un contracte amb un soci.
    """,
    "version": "24.5.0",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "giscedata_facturacio_comer",
        "giscedata_lectures_estimacio",
        "giscedata_polissa_category",
        "giscedata_switching_comer",
    ],
    "test_depends": [
        "giscedata_tarifas_peajes_20150101",
        "giscedata_tarifas_peajes_20160101",
        "giscedata_tarifas_peajes_20170101",
        "giscedata_tarifas_peajes_20180101",
    ],
    "init_xml": ["data/res_partner_data.xml"],
    "demo_xml": [
        "demo/res_partner_demo_data.xml",
    ],
    "update_xml": [
        "data/giscedata_facturacio_data.xml",
        "data/giscedata_polissa_category_data.xml",
        "data/giscedata_som_soci_data.xml",
        "data/res_partner_data.xml",
        "data/somenergia_soci_data.xml",
        "views/giscedata_facturacio_view.xml",
        "views/giscedata_polissa_view.xml",
        "views/res_partner_view.xml",
        "views/somenergia_soci_view.xml",
        "wizard/wizard_subscribe_client_mailchimp.xml",
        "wizard/wizard_subscribe_soci_mailchimp.xml",
        "wizard/wizard_unsubscribe_soci_mailchimp.xml",
        "wizard/wizard_update_invoice_check_ov_visible_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
