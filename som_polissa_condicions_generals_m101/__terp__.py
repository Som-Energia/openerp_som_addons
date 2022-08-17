# -*- coding: utf-8 -*-
{
    "name": "Condicions generals Somenergia (model giscedata.switching)",
    "description": """Aquest mòdul afegeix les següents funcionalitats:
    * Afegir nou report i nova plantilla d'email pels casos M1 01 de CT per subrogació i canvis tècnics
    """,
    "version": "2.107.5",
    "author": "SomEnergia",
    "category": "SomEnergia",
    "depends":[
        "giscedata_switching",
        "som_polissa_condicions_generals",
        "c2c_webkit_report",
    ],
    "init_xml": [],
    "demo_xml": [],
    "update_xml":[
        "giscedata_polissa_condicions_generals_m101_report.xml",
        "giscedata_switching_data_m1.xml"
    ],
    "active": False,
    "installable": True
}
