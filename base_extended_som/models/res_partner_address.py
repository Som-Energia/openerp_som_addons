# -*- coding: utf-8 -*-

import datetime
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
    def check_mobile_or_landline(number):
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
         'El número de telèfon ha de tenir exactament 9 dígits numèrics i començar per 9 o 8.', ['phone']),  # noqa:E501
        (_check_mobile_number,
         'El número de mòbil ha de tenir exactament 9 dígits numèrics i començar per 6 o 7.', ['mobile']),  # noqa:E501
    ]

    # This method is used to set default values for phone and mobile prefixes to Spain's codes
    def _get_default_prefix(self, cr, uid, context=None):
        """Return the default phone and mobile prefixes for Spain."""
        if context is None:
            context = {}
        res = self.pool.get('res.phone.national.code').search(
            cr, uid, [('name', '=', '+34')], limit=1, context=context)
        return res and res[0] or None

    def write(self, cr, uid, ids, vals, context=None, check=True):
        """Override write method to set default prefixes if not provided and
        to ensure phone and mobile numbers are in their correct fields."""

        if 'phone' in vals and 'phone_prefix' not in vals:
            vals['phone_prefix'] = self._get_default_prefix(cr, uid, context)
        if 'mobile' in vals and 'mobile_prefix' not in vals:
            vals['mobile_prefix'] = self._get_default_prefix(cr, uid, context)

        if 'phone' in vals and vals['phone']:
            phone_number = vals['phone']
            actual_mobile_number = self.browse(cr, uid, ids, context=context)[0].mobile
            if self.check_mobile_or_landline(phone_number) == 'mobile':
                if actual_mobile_number == phone_number:
                    vals.pop('phone')
                elif not actual_mobile_number:
                    vals['mobile'] = phone_number
                    vals.pop('phone')
                else:
                    # Estem intentant posar un telèfon fix en el camp de mòbil, que és diferent
                    # al telèfon fix que ja hi ha posat. El sobrescrivim i afegim una nota amb el vell  # noqa:E501
                    actual_notes = self.browse(cr, uid, ids, context=context)[0].notes or ''
                    today = datetime.date.today().strftime("%Y/%m/%d")
                    vals['notes'] = actual_notes + "\n{}: Telèofn mòbil substituit, l'antic mòbil era: {}".format(today, actual_mobile_number)  # noqa:E501
                    vals['mobile'] = phone_number

        if 'mobile' in vals and vals['mobile']:
            mobile_number = vals['mobile']
            actual_phone_number = self.browse(cr, uid, ids, context=context)[0].phone
            if self.check_mobile_or_landline(mobile_number) == 'landline':
                if actual_phone_number == mobile_number:
                    vals.pop('mobile')
                elif not actual_phone_number:
                    vals['phone'] = mobile_number
                    vals.pop('mobile')
                else:
                    # Estem intentant posar un telèfon fix en el camp de mòbil, que és diferent
                    # al telèfon fix que ja hi ha posat. El sobrescrivim i afegim una nota amb el vell  # noqa:E501
                    actual_notes = self.browse(cr, uid, ids, context=context)[0].notes or ''
                    today = datetime.date.today().strftime("%Y/%m/%d")
                    vals['notes'] = actual_notes + "\n{}: Telèofn fix substituit, l'antic telèfon era: {}".format(today, actual_phone_number)  # noqa:E501
                    vals['phone'] = mobile_number

        return super(ResPartnerAddress, self).write(
            cr, uid, ids, vals, context=context, check=check)

    _defaults = {
        'phone_prefix': _get_default_prefix,
        'mobile_prefix': _get_default_prefix,
    }


ResPartnerAddress()
