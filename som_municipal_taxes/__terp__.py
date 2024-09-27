# -*- coding: utf-8 -*-

{
    'name': 'Som municipal taxes',
    'description': 'Mòdul per gestionar el pagament del impost municipal',
    'version': '0.1',
    'category': 'Som Energia module',
    'website': 'https://github.com/Som-Energia/openerp-som-addons',
    'author': 'Som Energia SCCL',
    'license': 'AGPL-3',
    'active': False,
    'installable': True,
    'depends': [
        'base',
        'giscedata_municipal_taxes',
    ],
    'init_xml': [],
    'update_xml': [
        'data/som_municipal_taxes_data.xml',
        'views/som_municipal_taxes_config_view.xml',
        'wizard/wizard_creacio_remesa_pagament_taxes.xml',
        'security/som_municipal_taxes_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo_xml': [
        'tests/som_municipal_taxes_demo.xml',
    ]
}