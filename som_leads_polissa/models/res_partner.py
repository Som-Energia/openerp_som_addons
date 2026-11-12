# -*- coding: utf-8 -*-

from osv import osv, fields


class ResPartner(osv.osv):

    _name = "res.partner"
    _inherit = "res.partner"

    _columns = {
        "referral_source": fields.char("Com ens ha conegut", size=255),
    }


ResPartner()
