# -*- coding: utf-8 -*-
{
    "name": "Som Energia billing extension",
    "description": """SomEnergia billing extension""",
    "version": "0-dev",
    "author": "Som Energia",
    "category": "Master",
    "depends": [
        "base",
        "remeses_base",
        "giscedata_remeses",
        "giscedata_facturacio_comer",
        "giscedata_facturacio_impagat",
        "giscedata_facturacio_comer_bono_social",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "giscedata_facturacio_view.xml",
        "payment_order_data.xml",
        "wizard/wizard_change_payment_type_view.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
