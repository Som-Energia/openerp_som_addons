# -*- coding: utf-8 -*-
{
    "name": "Automatització del procés de facturació",
    "description": """
    Aquest mòdul fa:
        * Poder definir un workflow de tasques, activades o no, per automatitzar el procés de facturació.
    """,  # noqa: E501
    "version": "0.dev",
    "author": "SOM ENERGIA",
    "category": "SomEnergia",
    "depends": [
        "giscedata_facturacio",
        # "giscedata_facturacio_comer_som",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "som_autofactura_task_view.xml",
        "som_autofactura_data.xml",
        "wizard/wizard_autofactura.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
