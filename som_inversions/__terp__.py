# -*- coding: utf-8 -*-
{
    "name": "Mòdul d'inversions de socis",
    "description": """
    This module provide :
        * Creació del mode de pagament per inversions
        * Creació de la seqüència per les inversions
        * Creació de nou camp de bank al partner per guardar-hi el compte
          bancari on es cobraran els interessos de les inversions
        * Creació d'impost per representar el % de retorn d'inversió
    """,
    "version": "0-dev",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "som_partner_account",
        "account_payment",
        "l10n_ES_remesas",
        "account",
        "c2c_webkit_report",
        "giscedata_facturacio",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "partner_view.xml",
        "som_inversions_data.xml",
        "som_inversions_report.xml",
        "payment_view.xml",
        "wizard/wizard_liquidacio_interessos_view.xml",
        "security/som_inversions_security.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
