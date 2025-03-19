# -*- coding: utf-8 -*-

from osv import fields, osv


class ResPartner(osv.osv):
    """Modifiquem res_partner per poder assignar un bank on cobrar els
    interessos de les inversions"""

    _name = "res.partner"
    _inherit = "res.partner"

    _columns = {
        "bank_inversions": fields.many2one("res.partner.bank", "Banc interessos", required=False),
    }


ResPartner()
