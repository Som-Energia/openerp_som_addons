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
        "base_extended",
        "partner_representante",
        "poweremail",
        "giscere_cil",
        "giscere_polissa",
        "giscere_facturacio",
        "base_iban",
        "giscere_mhcil",
    ],
    'init_xml': [],
    'update_xml': [
        "data/somre_ov_signed_documents_data.xml",
        "data/email_template_data.xml",
        "views/somre_ov_users_view.xml",
        "wizard/wizard_create_change_password_view.xml",
        "wizard/wizard_create_somre_ov_users.xml",
        "security/ir.model.access.csv",
    ],
    'demo_xml': [
        "demo/res_partner_demo.xml",
        "demo/somre_ov_users_demo.xml",
        "demo/giscere_instalacio_demo.xml",
        "demo/giscere_facturacio_demo.xml",
        "demo/giscere_mhcil_demo.xml",
        "demo/giscere_previsio_publicada_demo.xml"
    ],
}
