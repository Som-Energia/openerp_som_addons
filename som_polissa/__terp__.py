# -*- coding: utf-8 -*-
{
    "name": "Funcions de suport a polissa per SOM",
    "description": """
    This module provide :
        * Pestanya de logs de Gestió Endarrerida
    """,
    "version": "24.5.0",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "giscedata_butlletins",
        "giscedata_polissa",
        "giscedata_polissa_comer",
        "giscedata_polissa_category",
        "giscedata_facturacio",
        "giscedata_polissa_responsable",
        "giscedata_facturacio_comer",
        "giscedata_facturacio_suspesa",
        "giscedata_facturacio_impagat",
        "giscedata_facturacio_impagat_comer",
        "giscedata_facturacio_bateria_virtual",
        "som_switching",
        "base_bank_extended",
        "l10n_ES_remesas",
        "www_base",
        "giscedata_repercussio_mecanismo_ajuste_gas",
    ],
    "init_xml": [],
    "demo_xml": ["tests/som_polissa_demo.xml"],
    "update_xml": [
        "giscedata_polissa_view.xml",
        "som_polissa_report.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_gestio_text_to_polissa_view.xml",
        "som_polissa_data.xml",
        "som_polissa_report.xml",
        "wizard/wizard_massive_category_to_polissa_view.xml",
        "giscedata_cups_view.xml",
        "wizard/wizard_import_ref_cadastral_from_csv_view.xml",
        "wizard/wizard_add_cut_off_to_polissa_from_csv_view.xml",
        "wizard/wizard_generate_cau_migration_file_view.xml",
        "giscedata_autoconsum_view.xml"
    ],
    "active": False,
    "installable": True,
}
