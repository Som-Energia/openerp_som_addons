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
        'giscedata_polissa_crm',
        'giscedata_facturacio_comer_bono_social',
        'som_account_invoice_pending',
        'som_polissa',
        'giscedata_atc',
    ],
    'init_xml': [],
    'demo_xml': [
        'demo/som_consulta_pobresa_demo.xml',
    ],
    'update_xml': [
        'views/som_consulta_pobresa_view.xml',
        'views/agrupacio_supramunicipal_view.xml',
        'wizard/wizard_crear_consulta_pobresa.xml',
        'data/agrupacio_supramunicipal_data.xml',
        'security/ir.model.access.csv',
    ],
}
