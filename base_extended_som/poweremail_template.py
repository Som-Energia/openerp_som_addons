# -*- coding: utf-8 -*-
from osv import osv


class poweremail_templates(osv.osv):
    _inherit = "poweremail.templates"

    _defaults = {
        "inline": lambda *a: True
    }


poweremail_templates()
