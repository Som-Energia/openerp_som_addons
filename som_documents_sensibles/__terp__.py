# -*- coding: utf-8 -*-
{
    "name": "Documents sensibles for Som Energia",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
  * Afegeix el model de dades per a clients electrodependents
""",
    "version": "2.103.13",
    "author": "SOMEnergia",
    "category": "Master",
    "depends": [
        "base",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "som_documents_sensibles_view.xml",
        "som_documents_sensibles_data.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True,
}
