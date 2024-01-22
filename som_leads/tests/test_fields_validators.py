# -*- coding: utf-8 -*-
from destral import testing
import unittest
from destral.transaction import Transaction
from expects import *
from ..validators.fields_validators import FieldsValidators

class FieldsValidatorsTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.leads_obj = self.openerp.pool.get('som.soci.crm.lead')

    def tearDown(self):
        self.txn.stop()

    def test__validate_vat__ok(self):

        validator = FieldsValidators()
        # test correct dni
        result1 = validator.validate_vat('ES41670640E')
        # test correct nie
        result2 = validator.validate_vat('Y5871952C')

        self.assertTrue(result1)
        self.assertTrue(result2)

    def test__validate_vat__not_ok(self):

        validator = FieldsValidators()
        # test vat with erroneous letter
        result = validator.validate_vat('ES41670640Q')
        # test vat with erroneous format 
        result1 = validator.validate_vat('E5432564Le43')
        # test vat with wrong characters
        result2 = validator.validate_vat(' E541670640E')
        result3 = validator.validate_vat('E54167*640E')
        # test vat without ES at the begining
        result4 = validator.validate_vat('UX41670640Q')

        self.assertFalse(result)
        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)
        self.assertFalse(result4)	

    def test__validate_email__ok(self):

        validator = FieldsValidators()
        # test correct email
        result1 = validator.validate_email('abc-d@mail.com')
        result2 = validator.validate_email('abc.def@mail.com')
        result3 = validator.validate_email('abc@mail.com')
        result4 = validator.validate_email('abc_def@mail.com')
        result5 = validator.validate_email('abc.def@mail.cc')
        result6 = validator.validate_email('abc.def@mail-archive.com')
        result7 = validator.validate_email('abc.def@mail.org')
        result8 = validator.validate_email('abc.def@mail.com')

        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(result3)
        self.assertTrue(result4)
        self.assertTrue(result5)
        self.assertTrue(result6)
        self.assertTrue(result7)
        self.assertTrue(result8)

    def test__validate_email__not_ok(self):      

        validator = FieldsValidators()
        # test wrong email
        result1 = validator.validate_email('abc-@mail.com')
        result2 = validator.validate_email('abc..def@mail.com')
        result3 = validator.validate_email('.abc@mail.com')
        result4 = validator.validate_email('abc#def@mail.com')
        result5 = validator.validate_email("abc.def@mail.c")
        result6 = validator.validate_email("abc.def@mail#archive.com")
        result7 = validator.validate_email("abc.def@mail")
        result8 = validator.validate_email("abc.def@mail..com")
        result9 = validator.validate_email("-abc.def@mail.com")
 
        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)
        self.assertFalse(result4)
        self.assertFalse(result5)
        self.assertFalse(result6)
        self.assertFalse(result7)
        self.assertFalse(result8)
        self.assertFalse(result9)

    def test__validate_phone_ok(self):
        validator = FieldsValidators()
        #test Catalunya phones
        result1 = validator.validate_phone('972538345')
        result2 = validator.validate_phone('936940359')
        #test Madrid phones
        result3 = validator.validate_phone('919930821')
        #test Canarias phones
        result4 = validator.validate_phone('922777288')
        #test mobile phone
        result5 = validator.validate_phone('675432198')

        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(result3)
        self.assertTrue(result4)
        self.assertTrue(result5)
    
    def test__validate_phone_not_ok(self):
        validator = FieldsValidators()
        # test USA phones
        result1 = validator.validate_phone('1800746-5020')
        result2 = validator.validate_phone('1-212-324-4152')
        #test invalid format phones
        result3 = validator.validate_phone('97232432132')
        result4 = validator.validate_phone('97232')
        result5 = validator.validate_phone('97232%878')
        result6 = validator.validate_phone('754322211')

        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)
        self.assertFalse(result4)
        self.assertFalse(result5)
        self.assertFalse(result6)
        
    def test__validate_phone_not_ok(self):
        validator = FieldsValidators()
        # test USA phones
        result1 = validator.validate_phone('1800746-5020')
        result2 = validator.validate_phone('1-212-324-4152')
        #test invalid format phones
        result3 = validator.validate_phone('97232432132')
        result4 = validator.validate_phone('97232')
        result5 = validator.validate_phone('97232%878')
        result6 = validator.validate_phone('754322211')

        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)
        self.assertFalse(result4)
        self.assertFalse(result5)
        self.assertFalse(result6)

    def test__validate_iban_ok(self):
        
        validator = FieldsValidators()
        # test valid iban       
        result1 = validator.validate_iban('NL11ABNA5245129183')
        result2 = validator.validate_iban('ES1220385643027356529429')

        self.assertTrue(result1)
        self.assertTrue(result2)

    def test__validate_iban_not_ok(self):
        
        validator = FieldsValidators()
        # test invalid iban       
        result1 = validator.validate_iban('NL11ABNA5245129189')
        result2 = validator.validate_iban('ES1220385643027356529423')

        self.assertFalse(result1)
        self.assertFalse(result2)

    def test__validate_state_ok(self):
        validator = FieldsValidators()

        state_id = 20 # Girona (prov)
        result = validator.validate_state(self.cursor, self.uid, self.leads_obj, state_id)

        self.assertTrue(result)

    def test__validate_state_not_ok(self):
        validator = FieldsValidators()

        result = validator.validate_state(self.cursor, self.uid, self.leads_obj, 0)

        self.assertFalse(result)

    def test__validate_city_ok(self):
        validator = FieldsValidators()

        state_id = 20 # Girona province
        city_id = 2524 # Girona
        result = validator.validate_city(self.cursor, self.uid, self.leads_obj, state_id, city_id)

        self.assertTrue(result)

    def test__validate_city_not_ok(self):
        validator = FieldsValidators()
        bad_city_id = 0
        bad_state_id = 0
        state_id = 20 # Girona province
        city_within_state_id = 2512 # Figueres
        city_out_of_state_id = 4367 # Mostoles

        self.assertFalse(validator.validate_city(self.cursor, self.uid, self.leads_obj,
            state_id, bad_city_id # Bad city!!
        ))
        self.assertFalse(validator.validate_city(self.cursor, self.uid, self.leads_obj,
            bad_state_id, city_within_state_id # Bad state!!
        ))
        self.assertFalse(validator.validate_city(self.cursor, self.uid, self.leads_obj,
            state_id, city_out_of_state_id # City of another state!!
        ))

    def test__validate_payment_method_ok(self):
        validator = FieldsValidators()
        
        result1 = validator.validate_payment_method(self.cursor, self.uid, self.leads_obj, "RECIBO_CSB")
        result2 = validator.validate_payment_method(self.cursor, self.uid, self.leads_obj, "TRANSFERENCIA_CSB")
        result3 = validator.validate_payment_method(self.cursor, self.uid, self.leads_obj, "TPV")
        
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(result3)

    def test__validate_payment_method_not_ok(self):
        validator = FieldsValidators()
    
        result1 = validator.validate_payment_method(self.cursor, self.uid, self.leads_obj, "JABUGO")
    
        self.assertFalse(result1)