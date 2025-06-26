# -*- coding: utf-8 -*-

from destral import testing
from osv.orm import FieldsValidationException


class TestBaseExtendedSom(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.rpa_obj = self.openerp.pool.get("res.partner.address")
        super(TestBaseExtendedSom, self).setUp()

    def test_check_phone_number_with_config_disabled(self):
        """Test that phone numbers are checked correctly."""

        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "phone": "111",
            "mobile": "987654321",
        })
        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("phone", "=", "111")])
        self.assertGreater(len(rp_ids), 0, "Every phone number should be valid.")

    def test_check_phone_number_with_config_enabled(self):
        # Enable phone number checking
        res_obj = self.openerp.pool.get("res.config")
        res_obj.set(self.cursor, self.uid, "check_phone_number", "1")

        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "phone": "222",
            })

        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "phone": "600000000",
            })

        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "phone": "972000000",
        })
        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("phone", "=", "972000000")])
        self.assertGreater(len(rp_ids), 0, "Phone number should be valid.")

    def test_check_mobile_number_with_config_disabled(self):
        """Test that mobile numbers are checked correctly."""

        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "mobile": "111",
        })
        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("mobile", "=", "111")])
        self.assertGreater(len(rp_ids), 0, "Every mobile number should be valid.")

    def test_check_mobile_number_with_config_enabled(self):
        # Enable mobile number checking
        res_obj = self.openerp.pool.get("res.config")
        res_obj.set(self.cursor, self.uid, "check_mobile_number", "1")

        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "mobile": "222",
            })

        with self.assertRaises(FieldsValidationException):
            self.rpa_obj.write(self.cursor, self.uid, [1], {
                "mobile": "972000000",
            })

        self.rpa_obj.write(self.cursor, self.uid, [1], {
            "mobile": "600000000",
        })
        rp_ids = self.rpa_obj.search(self.cursor, self.uid, [("mobile", "=", "600000000")])
        self.assertGreater(len(rp_ids), 0, "mobile number should be valid.")
