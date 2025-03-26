# -*- coding: utf-8 -*-
{
    "name": "Procediments d'impagats específics de Som Energia",
    "description": """Mòdul per a la gestió dels impagaments de contractes
        especifics de SomEngergia""",
    "version": "24.5.0",
    "author": "Som Energia SCCL",
    "category": "Master",
    "depends": [
        "account_invoice_pending",
        "giscedata_facturacio",
        "l10n_ES_cobros_ventanilla",
        "powersms",
        "giscedata_facturacio_impagat_comer",
        "poweremail",
        "som_polissa",
        "custom_search",
        "crm",
        "giscedata_polissa_crm",
        "giscedata_facturacio_comer_bono_social",
        "giscedata_atc",
        "giscedata_facturacio_comer_som",
        "som_generationkwh",
    ],
    "init_xml": [
    ],
    "demo_xml": [
        "demo/som_account_invoice_pending_demo_data.xml",
        "demo/som_consulta_pobresa_demo.xml",
    ],
    "update_xml": [
        "data/som_account_invoice_pending_data.xml",
        "data/custom_search_data.xml",
        "data/agrupacio_supramunicipal_data.xml",
        "data/som_consulta_pobresa_data.xml",
        "wizard/wizard_returned_invoices_export.xml",
        "wizard/wizard_unlink_sms_pending_history_view.xml",
        "wizard/wizard_tugesto_invoices_export.xml",
        "wizard/wizard_change_pending_view.xml",
        "wizard/wizard_crear_consulta_pobresa.xml",
        "security/ir.model.access.csv",
        "views/account_invoice_pending_view.xml",
        "views/som_consulta_pobresa_view.xml",
        "views/agrupacio_supramunicipal_view.xml",
    ],
    "active": False,
    "installable": True,
}
