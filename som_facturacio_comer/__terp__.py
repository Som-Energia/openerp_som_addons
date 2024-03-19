# -*- coding: utf-8 -*-
{
    "name": "Funcions de suport a facturació comer per SOM",
    "description": """
    This module provide :
        * Validació propia a giscedata_facturacio_comer
    """,
    "version": "0-dev",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "giscedata_facturacio_comer",
        "giscedata_polissa_category",
        "som_polissa",
        "som_switching",
        "som_generationkwh",
        "giscedata_repercussio_mecanismo_ajuste_gas",
        "giscedata_facturacio_impagat_comer",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "data/res_config_data.xml",
        "giscedata_facturacio_validation_data.xml",
        "giscedata_facturacio_contracte_lot_view.xml",
        "security/ir.model.access.csv",
        "wizard/wizard_revert_incident_fact_contracte_lot_view.xml",
        "wizard/wizard_open_factures_send_mail_view.xml",
        "wizard/wizard_informe_factures_dades_desagregades_view.xml",
        "giscedata_facturacio_contracte_lot_view.xml",
        "giscedata_facturacio_factura_view.xml",
        "giscedata_facturacio_data.xml",
        "giscedata_lectures_view.xml",
        "giscedata_polissa_view.xml",
        "giscedata_facturacio_view.xml",
    ],
    "active": False,
    "installable": True,
}
