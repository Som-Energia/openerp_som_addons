# -*- coding: utf-8 -*-
from osv import osv, fields


class ResPartner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"

    _columns = {
        "creditcard_ids": fields.one2many(
            "res.partner.creditcard", "partner_id", "Targetes"
        )
    }


ResPartner()
