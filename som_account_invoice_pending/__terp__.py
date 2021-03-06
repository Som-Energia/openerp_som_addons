# -*- coding: utf-8 -*-
{
    "name": "Procediments d'impagats específics de Som Energia",
    "description": """Mòdul per a la gestió dels impagaments de contractes 
        especifics de SomEngergia""",
    "version": "0.1.2",
    "author": "Som Energia SCCL",
    "category": "Master",
    "depends":[
        "giscedata_facturacio_comer_bono_social",
        "account_invoice_pending",
        "giscedata_facturacio",
        "l10n_ES_cobros_ventanilla",
        "powersms",
        "www_som",
        "poweremail"
   ],
    "init_xml": [],
    "demo_xml": [
        "som_account_invoice_pending_demo.xml",
    ],
    "update_xml":[
        "som_account_invoice_pending_data.xml",
        "wizard/wizard_returned_invoices_export.xml",
        "wizard/wizard_unlink_sms_pending_history_view.xml",
        "security/ir.model.access.csv",
        "account_invoice_pending_view.xml",
    ],
    "active": False,
    "installable": True
}
