# -*- coding: utf-8 -*-
import re
import phonenumbers
import vatnumber
from stdnum import iban as iban_validator

class FieldsValidators():

    def __init__(self):
        pass

    def validate_vat(self, vat):
        if not isinstance(vat, (str, unicode)):
            return False
        if not vat.startswith('ES'):
            vat = 'ES{}'.format(vat)
        return vatnumber.check_vat(vat)

    def validate_phone(self, phone):
        phone_with_country_code = phone, 'ES'
        try:
            return phonenumbers.is_valid_number(
                phonenumbers.parse(*phone_with_country_code)
            )
        except phonenumbers.NumberParseException:
            return False

    def validate_email(self, email):
        if not re.match(r"^([A-Za-z0-9]+[\.\-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+", email):
            return False
        return True
           
    def validate_iban(self, iban):
        return iban_validator.is_valid(iban)
    
    def validate_state(self, cursor, uid, obj, state_id):
        state_obj = obj.pool.get('res.country.state')
        state = state_obj.read(cursor, uid, state_id)
        return bool(state)

    def validate_city(self, cursor, uid, obj, state_id, city_id):
        city_obj = obj.pool.get('res.municipi')
        city = city_obj.read(cursor, uid, city_id)
        if not city:
            return False
        if city['state'][0] != state_id:
            return False
        return True

    def validate_payment_method(self,cursor, uid, obj, payment_method):
        payment_obj = obj.pool.get('payment.type')
        payment_ids = payment_obj.search(cursor, uid, [('code','=',payment_method)])
        if not payment_ids:
            return False
        return True
