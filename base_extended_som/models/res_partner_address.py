# -*- coding: utf-8 -*-

from osv import fields, osv


class ResPartnerAddress(osv.osv):
    """Afegim el codi nacional de telèfon a la taula res.partner.address"""

    _name = "res.partner.address"
    _inherit = "res.partner.address"

    _columns = {
        'phone_prefix': fields.many2one(
            'res.phone.national.code', 'Prefix', required=False),
        'mobile_prefix': fields.many2one(
            'res.phone.national.code', 'Prefix', required=False),
    }

    # This method is used to set default values for phone and mobile prefixes to Spain's codes
    def _get_default_prefix(self, cr, uid, context=None):
        """Return the default phone and mobile prefixes for Spain."""
        if context is None:
            context = {}
        res = self.pool.get('res.phone.national.code').search(
            cr, uid, [('code', '=', '34')], limit=1, context=context)
        return res

    _defaults = {
        'phone_prefix': _get_default_prefix,
        'mobile_prefix': _get_default_prefix,
    }


ResPartnerAddress()
