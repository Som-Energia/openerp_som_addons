# -*- coding: utf-8 -*-
{
    "name": "Facturación 10% IVA de Som",
    "description": """Facturación al 10% de IVA sobre los componentes de la factura eléctrica

  Este módulo introduce un modelo de datos para guardar en el ERP la media aritmética del precio medio de OMIE
  a nivel mensual, en barras de central.
  """,  # noqa: E501
    "version": "0-dev",
    "author": "GISCE",
    "category": "GISCEMaster",
    "depends": ["base", "giscedata_facturacio_iva_10"],
    "init_xml": [],
    "demo_xml": [
        "demo/giscedata_facturacio_iva_10_demo.xml",
    ],
    "update_xml": [],
    "active": False,
    "installable": True,
}
