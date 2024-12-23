# -*- coding: utf-8 -*-
{
    "name": "Customitzacions per AUVIDIs (Serveis de generació) per a SOM",
    "description": """
    """,
    "version": "0-dev",
    "author": "GISCE",
    "category": "SomEnergia",
    "depends": [
        "base",
        "giscedata_serveis_generacio",
        "giscedata_polissa_category",
        "som_indexada",
        "giscedata_facturacio_indexada_som"
 
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "giscedata_polissa_view.xml",
        "giscedata_serveis_generacio_data.xml",
        "giscedata_serveis_generacio_view.xml",
        "wizard/wizard_change_to_indexada_auvidi_multi.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
