# -*- coding: utf-8 -*-

from osv import fields, osv


class ResPartnerAddress(osv.osv):
    """Afegim el codi nacional de telèfon a la taula res.partner.address"""

    _name = "res.partner.address"

    _columns = {
        'phone_prefix': fields.one2many(
            'res.phone.national.code', 'partner_address_id'),
        'mobile_prefix': fields.one2many(
            'res.phone.national.code', 'partner_address_id'),
    }


ResPartnerAddress()
