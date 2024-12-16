# -*- coding: utf-8 -*-

{
    'name': 'somre_ov_module',
    'description': 'Modul de som representa com a suport de la oficina virtual',
    'version': '1.0',
    'category': 'Som Energia module',
    'website': 'https://github.com/Som-Energia/openerp-som-addons',
    'author': 'Som Energia SCCL',
    'license': 'AGPL-3',
    'active': False,
    'installable': True,
    'depends': [
        'base',
    ],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
    ],
    'demo_xml': [
    ],
}
