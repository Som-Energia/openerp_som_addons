# -*- coding: utf-8 -*-

{
    'name': 'SomEnergia Tarifa social',
    'description': 'Mòdul que conté la lògica per posar i treure la tarifa social',
    'version': '24.5.0',
    'category': 'Som Energia module',
    'website': 'https://github.com/Som-Energia/openerp-som-addons',
    'author': 'Som Energia SCCL',
    'license': 'AGPL-3',
    'active': False,
    'installable': True,
    'depends': [
        'base',
        'giscedata_facturacio',
        'poweremail',
        'som_indexada',
        'som_polissa',
    ],
    'init_xml': [],
    'update_xml': [
        'data/pricelist_social_data.xml',
        'data/poweremail_templates.xml',
        'security/ir.model.access.csv',
        'wizards/wizard_change_tariff_social_view.xml',
    ],
    'demo_xml': [
    ],
}
