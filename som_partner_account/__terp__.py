# -*- coding: utf-8 -*-
{
    "name": "Creació de comptes comptables segons codi del partner",
    "description": """
    This module provide :
        * Creació de comptes comptables per partner.
    """,
    "version": "0-dev",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "base_extended",
        "account_payment_extension",
        "som_partner_seq",
        "som_polissa_soci",
        "l10n_chart_ES",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ["partner_view.xml", "account_chart.xml", "partner_data.xml"],
    "active": False,
    "installable": True,
}
