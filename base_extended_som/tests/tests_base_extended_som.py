# -*- coding: utf-8 -*-

from destral import testing
from osv.orm import FieldsValidationException
import datetime


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

        rp_ids = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "972000000",
            "mobile": "600000000",
        })
        self.assertTrue(rp_ids, "Default prefix works.")

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

    def test_write_without_prefixes(self):
        """Test that writing without prefixes sets default prefixes."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "972000000",
            "mobile": "600000000",
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.phone_prefix.id, self.spanish_prefix,
            "Phone prefix should be set to Spanish prefix."
        )
        self.assertEqual(
            rp.mobile_prefix.id, self.spanish_prefix,
            "Mobile prefix should be set to Spanish prefix."
        )

    def test_write_with_prefixes_spain(self):
        """Test that writing with prefixes retains provided prefixes."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "972000000",
            "mobile": "600000000",
            "phone_prefix": self.spanish_prefix,
            "mobile_prefix": self.spanish_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.phone_prefix.id, self.spanish_prefix,
            "Phone prefix should be retained as Spanish prefix."
        )
        self.assertEqual(
            rp.mobile_prefix.id, self.spanish_prefix,
            "Mobile prefix should be retained as Spanish prefix."
        )

    def test_write_with_prefixes_other(self):
        """Test that writing with non-Spanish prefixes retains provided prefixes."""
        self.us_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base", "res_phone_national_code_data_1"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "5551234567",
            "mobile": "5557654321",
            "phone_prefix": self.us_prefix,
            "mobile_prefix": self.us_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.phone_prefix.id, self.us_prefix,
            "Phone prefix should be retained as US prefix."
        )
        self.assertEqual(
            rp.mobile_prefix.id, self.us_prefix,
            "Mobile prefix should be retained as US prefix."
        )

    def test_write_landline_phone_in_phone_field(self):
        """Test that writing a landline number into the phone field is handled correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "972000000",
            "phone_prefix": self.spanish_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.phone, "972000000",
            "Phone field should contain the landline number written into it."
        )
        self.assertEqual(
            rp.mobile, False,
            "Mobile field should remain empty when a landline number is written into phone field."
        )

    def test_write_mobile_phone_in_mobile_field(self):
        """Test that writing a mobile number into the mobile field is handled correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "mobile": "600000000",
            "mobile_prefix": self.spanish_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.mobile, "600000000",
            "Mobile field should contain the mobile number written into it."
        )
        self.assertEqual(
            rp.phone, False,
            "Phone field should remain empty when a mobile number is written into mobile field."
        )

    def test_write_mobile_phone_in_phone_field(self):
        """Test that writing a mobile number into the phone field is handled correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "600000000",
            "phone_prefix": self.spanish_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.phone, False,
            "Phone field should be cleared when a mobile number is written into it."
        )
        self.assertEqual(
            rp.mobile, "600000000",
            "Mobile field should contain the mobile number written into phone field."
        )

    def test_write_phone_landline_in_mobile_field(self):
        """Test that writing a landline number into the mobile field is handled correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "mobile": "972000000",
            "mobile_prefix": self.spanish_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.mobile, False,
            "Mobile field should be cleared when a landline number is written into it."
        )
        self.assertEqual(
            rp.phone, "972000000",
            "Phone field should contain the landline number written into mobile field."
        )

    def test_write_phone_mobile_in_mobile_field(self):
        """Test that writing a mobile number into the mobile field is handled correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "mobile": "600000000",
            "mobile_prefix": self.spanish_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.mobile, "600000000",
            "Mobile field should contain the mobile number written into it."
        )
        self.assertEqual(
            rp.phone, False,
            "Phone field should remain empty when a mobile number is written into mobile field."
        )

    def test_write_phone_landline_in_phone_field(self):
        """Test that writing a landline number into the phone field is handled correctly."""
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "972000000",
            "phone_prefix": self.spanish_prefix,
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.phone, "972000000",
            "Phone field should contain the landline number written into it."
        )
        self.assertEqual(
            rp.mobile, False,
            "Mobile field should remain empty when a landline number is written into phone field."
        )

    def test_write_landline_phone_in_mobile_field_with_existing_mobile(self):
        """Test that writing a landline number into the mobile field with existing mobile is handled correctly."""  # noqa:E501
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "mobile": "600000000",
            "mobile_prefix": self.spanish_prefix,
        })

        # Now write a landline number into the mobile field
        self.rpa_obj.write(self.cursor, self.uid, [rp_id], {
            "mobile": "972000000",
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.mobile, False,
            "Mobile field should be cleared when a landline number is written into it."
        )
        self.assertEqual(
            rp.phone, "972000000",
            "Phone field should contain the landline number written into mobile field."
        )

    def test_write_landline_phone_in_mobile_field_with_existing_phone(self):
        """Test that writing a landline number into the mobile field with existing phone is handled correctly."""  # noqa:E501
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "phone": "972000000",
            "phone_prefix": self.spanish_prefix,
        })

        # Now write a landline number into the mobile field
        self.rpa_obj.write(self.cursor, self.uid, [rp_id], {
            "mobile": "872000000",
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.mobile, False,
            "Mobile field should be cleared when a landline number is written into it."
        )
        self.assertEqual(
            rp.phone, "872000000",
            "Phone field should contain the landline number written into mobile field."
        )
        today = datetime.date.today().strftime("%Y/%m/%d")
        self.assertEqual(
            rp.notes, "{}: Telèofn fix substituit, l'antic telèfon era: 972000000".format(today),
            "Notes should contain information about the phone number change."
        )

    def test_write_mobile_phone_in_phone_field_with_existing_mobile(self):
        """Test that writing a mobile number into the phone field with existing mobile is handled correctly."""  # noqa:E501
        self.spanish_prefix = self.ir_obj.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_phone_national_code_data_34"
        )[1]

        rp_id = self.rpa_obj.create(self.cursor, self.uid, {
            "name": "Test Address",
            "mobile": "600000000",
            "mobile_prefix": self.spanish_prefix,
        })

        # Now write a mobile number into the phone field
        self.rpa_obj.write(self.cursor, self.uid, [rp_id], {
            "phone": "700000000",
        })

        rp = self.rpa_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(
            rp.phone, False,
            "Phone field should be cleared when a mobile number is written into it."
        )
        self.assertEqual(
            rp.mobile, "700000000",
            "Mobile field should contain the mobile number written into phone field."
        )
        today = datetime.date.today().strftime("%Y/%m/%d")
        self.assertEqual(
            rp.notes, "{}: Telèofn mòbil substituit, l'antic mòbil era: 600000000".format(today),
            "Notes should contain information about the mobile number change."
        )
