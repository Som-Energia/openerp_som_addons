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

    @staticmethod
    def check_mobile_or_landline(cursor, uid, number):
        """docstring
        Check if the spanish phone number is a valid landline or mobile number in Spain.
        Valid landline numbers start with 8 or 9 and have 9 digits.
        Valid mobile numbers start with 6 or 7 and have 9 digits.

        :param number: str, the phone number to check
        :return: str or bool, 'landline' if valid landline,
             'mobile' if valid mobile, False if invalid"""

        if number.isdigit() and len(number) == 9 and \
           (number.startswith('9') or number.startswith('8')):
            return 'landline'
        if number.isdigit() and len(number) == 9 and \
           (number.startswith('6') or number.startswith('7')):
            return 'mobile'
        return False

    def _check_phone_number(self, cr, uid, ids, context=None):
        """Check if the spanish phone number is valid."""
        if not int(self.pool.get('res.config').get(cr, uid, 'check_phone_number', '0')):
            return True

        for record in self.browse(cr, uid, ids, context=context):
            value = record.phone
            if not value:
                return True
            if record.phone_prefix.name != '+34':
                return True
            if self.check_mobile_or_landline(value) == 'landline':
                return True
            else:
                return False
        return True

    def _check_mobile_number(self, cr, uid, ids, context=None):
        """Check if the spanish mobile number is valid."""
        if not int(self.pool.get('res.config').get(cr, uid, 'check_mobile_number', '0')):
            return True
        for record in self.browse(cr, uid, ids, context=context):
            value = record.mobile
            if not value:
                return True
            if record.mobile_prefix.name != '+34':
                return True
            if self.check_mobile_or_landline(value) == 'mobile':
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
        return res and res[0] or None

    _defaults = {
        'phone_prefix': _get_default_prefix,
        'mobile_prefix': _get_default_prefix,
    }


ResPartnerAddress()
