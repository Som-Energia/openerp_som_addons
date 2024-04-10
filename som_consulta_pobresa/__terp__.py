# -*- coding: utf-8 -*-

{
    'name': 'som_consulta_pobresa',
    'description': """ Mòdul per gestionar les peticions de pobresa energètica
         dels contractes amb factures impades, als ajuntaments""",
    'version': '0.1',
    'category': 'Som Energia module',
    'website': 'https://github.com/Som-Energia/openerp-som-addons',
    'author': 'Som Energia SCCL',
    'license': 'AGPL-3',
    'active': False,
    'installable': True,
    'depends': [
        'crm',
        'giscedata_polissa',
    ],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'views/som_consulta_pobresa_view.xml',
    ],
    'demo_xml': [
        # 'demo/res_partner_demo.xml',
    ],
}
