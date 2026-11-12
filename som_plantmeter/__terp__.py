# -*- coding: utf-8 -*-
{
  "name": "Generationkwh production manager",
  "description": """Support for SomEnergia's plantmeter in GisceERP""",
  "version": "1.7.3",
  "author": "Som-Energia",
  "category": "Master",
  "depends": ['base'],
  "init_xml": [],
  "demo_xml": [],
  "update_xml": [
    "security/som_plantmeter.xml",
    "security/ir.model.access.csv",
    ],
  "active": False,
  "installable": True
}
