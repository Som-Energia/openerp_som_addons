# -*- coding: utf-8 -*-

from destral import testing
from osv.orm import FieldsValidationException


class TestBaseExtendedSom(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.rpa_obj = self.openerp.pool.get("res.partner.address")
        self.res_obj = self.openerp.pool.get("res.config")
        self.ir_obj = self.openerp.pool.get("ir.model.data")

        super(TestBaseExtendedSom, self).setUp()

    def test_check_phone_number_with_config_disabled(self):
        """Test that phone numbers are checked correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "phone": "111",
            "mobile": "987654321",
            "phone_prefix": self.spanish_prefix,
            "mobile_prefix": self.spanish_prefix,
        })

        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("phone", "=", "111")])
        self.assertGreater(len(rp_ids), 0, "Every phone number should be valid.")

    def test_check_phone_number_with_config_enabled(self):
        # Enable phone number checking
        self.res_obj.set(self.cursor, self.uid, "check_phone_number", "1")
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "phone": "222",
                "phone_prefix": self.spanish_prefix,
            })

        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "phone": "600000000",
                "phone_prefix": self.spanish_prefix,
            })
        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "phone": "972000000",
            "phone_prefix": self.spanish_prefix,
        })

        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("phone", "=", "972000000")])
        self.assertGreater(len(rp_ids), 0, "Phone number should be valid.")

    def test_check_mobile_number_with_config_disabled(self):
        """Test that mobile numbers are checked correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "mobile": "111",
            "mobile_prefix": self.spanish_prefix,
        })

        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("mobile", "=", "111")])
        self.assertGreater(len(rp_ids), 0, "Every mobile number should be valid.")

    def test_check_mobile_number_with_config_enabled(self):
        # Enable mobile number checking
        self.res_obj.set(self.cursor, self.uid, "check_mobile_number", "1")
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "mobile": "222",
                "mobile_prefix": self.spanish_prefix,
            })
        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "mobile": "972000000",
                "mobile_prefix": self.spanish_prefix,
            })
        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "mobile": "600000000",
            "mobile_prefix": self.spanish_prefix,
        })

        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("mobile", "=", "600000000")])
        self.assertGreater(len(rp_ids), 0, "mobile number should be valid.")

    def test_check_mobile_or_landline(self):
        """Test the check_mobile_or_landline method."""
        self.assertEqual(
            self.rpa_obj.check_mobile_or_landline("600000000"), "mobile",
            "600000000 should be recognized as a mobile number."
        )
        self.assertEqual(
            self.rpa_obj.check_mobile_or_landline("972000000"), "landline",
            "972000000 should be recognized as a landline number."
        )
        self.assertEqual(
            self.rpa_obj.check_mobile_or_landline("700000000"), "mobile",
            "700000000 should be recognized as a mobile number."
        )
        self.assertEqual(
            self.rpa_obj.check_mobile_or_landline("872000000"), "landline",
            "872000000 should be recognized as a landline number."
        )
        self.assertFalse(
            self.rpa_obj.check_mobile_or_landline("123456789"),
            "123456789 should not be recognized as a valid number."
        )
        self.assertFalse(
            self.rpa_obj.check_mobile_or_landline("abcdefghi"),
            "abcdefghi should not be recognized as a valid number."
        )
        self.assertFalse(
            self.rpa_obj.check_mobile_or_landline("97200000"),
            "97200000 should not be recognized as a valid number."
        )
        self.assertFalse(
            self.rpa_obj.check_mobile_or_landline("+34 972000000"),
            "+34 972000000 should not be recognized as a valid number."
        )
