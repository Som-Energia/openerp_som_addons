# -*- coding: utf-8 -*-
from osv import osv, fields


class poweremail_templates(osv.osv):
    _inherit = "poweremail.templates"

    _columns = {
        "sendgrid_category_ids": fields.many2many(
            "poweremail.sendgrid.category",
            "poweremail_sendgrid_category_poweremail_template_rel",
            "poweremail_template_id",
            "sendgrid_category_id",
            "SendGrid Category"
        ),
    }

    _defaults = {
        "inline": lambda *a: True
    }


poweremail_templates()
