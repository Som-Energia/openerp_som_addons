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

    def _check_phone_number(self, cr, uid, ids, context=None):
        """Check if the phone number is valid."""
        """Phone numbers in Spain have 9 digits and start with 9, 8, or 7."""
        if not int(self.pool.get('res.config').get(cr, uid, 'check_phone_number', '0')):
            return True

        for record in self.browse(cr, uid, ids, context=context):
            value = record.phone
            if not value:
                return True
            if value.isdigit() and len(value) == 9 and \
               (value.startswith('9') or value.startswith('8')
                    or value.startswith('7')):
                return True
            else:
                return False
        return True

    def _check_mobile_number(self, cr, uid, ids, context=None):
        """Check if the mobile number is valid."""
        """Mobile numbers in Spain start with 6 or 7 and have 9 digits."""
        if not int(self.pool.get('res.config').get(cr, uid, 'check_mobile_number', '0')):
            return True
        for record in self.browse(cr, uid, ids, context=context):
            value = record.mobile
            if not value:
                return True
            if value.isdigit() and len(value) == 9 and \
               (value.startswith('6') or value.startswith('7')):
                return True
            else:
                return False
        return True

    _constraints = [
        (_check_phone_number,
         'El número de telèfon ha de tenir exactament 9 dígits numèrics.', ['phone']),
        (_check_mobile_number,
         'El número de mòbil ha de tenir exactament 9 dígits numèrics.', ['mobile']),
    ]

    # This method is used to set default values for phone and mobile prefixes to Spain's codes
    def _get_default_prefix(self, cr, uid, context=None):
        """Return the default phone and mobile prefixes for Spain."""
        if context is None:
            context = {}
        res = self.pool.get('res.phone.national.code').search(
            cr, uid, [('name', '=', '+34')], limit=1, context=context)
        return res

    _defaults = {
        'phone_prefix': _get_default_prefix,
        'mobile_prefix': _get_default_prefix,
    }


ResPartnerAddress()
