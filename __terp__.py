{
    "name" : "Powerful SMS capabilities for Open ERP",
    "version" : "0.1",
    "author" : "Som Energia SCCL",
    "website" : "https://github.com/Som-Energia/powersms",
    "category" : "Added functionality",
    "depends" : ['base_extended'],
    "description": """Power SMS""",
    "demo_xml": [
        "tests/powersms_demo.xml",
    ],
    "init_xml": [],
    "update_xml": [
        'security/powersms_security.xml',
        'security/ir.model.access.csv',
        'powersms_core_view.xml',
        'powersms_template_view.xml',
        'powersms_smsbox_view.xml',
        'powersms_workflow.xml',
        'wizard/wizard_send_sms_view.xml',
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
