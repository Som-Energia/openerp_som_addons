# -*- coding: utf-8 -*-
{
    "name": "Funcions de suport a switching per SOM",
    "description": """
    This module provide :
        * Funció propia a pólissa (escull_llista_preus) per escollir tarifa a partir llistes de preus.  # noqa: E501
    """,
    "version": "2.107.6",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "som_polissa",
        "som_switching",
        "giscedata_facturacio_comer",
        "som_facturacio_comer",
        "giscedata_facturacio_switching",
        "som_indexada",
    ],
    "init_xml": [],
    "demo_xml": [
        "pricelist_demo_data.xml",
        "demo/som_facturacio_switching_demo.xml",
    ],
    "update_xml": [
        "wizard/wizard_gestio_text_to_polissa_view.xml",
        "wizard/wizard_model_list_from_file_data.xml",
        "facturacio_extra_view.xml",
        "giscedata_facturacio_importacio_linia_view.xml",
        "giscedata_facturacio_switching_error_data.xml",
        "wizard/wizard_delete_reimport_2001_f1_view.xml",
        "security/ir.model.access.csv",
        "giscedata_facturacio_switching_cron.xml",
        "wizard/wizard_refund_rectify_from_origin_view.xml",
        "giscedata_facturacio_switching_view.xml",
        "som_error_cron_f1_reimport_data.xml",
        "som_error_cron_f1_reimport_view.xml",
        "wizard/wizard_change_cron_reimport_days_view.xml",
    ],
    "active": False,
    "installable": True,
}
