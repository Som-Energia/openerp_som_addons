# -*- coding: utf-8 -*-
from destral import testing
from osv.orm import FieldsValidationException


class TestPoweremail(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.category_obj = self.openerp.pool.get("poweremail.sendgrid.category")
        self.template_obj = self.openerp.pool.get("poweremail.templates")
        self.mail_obj = self.openerp.pool.get("poweremail.mailbox")
        super(TestPoweremail, self).setUp()

    def test_category_name_validation(self):
        """Test that category name validation works."""

        # With ascii, it don't fail
        self.category_obj.create(self.cursor, self.uid, {
            "name": "Canvi de preus",
        })

        # With special characters, it fails
        with self.assertRaises(FieldsValidationException):
            self.category_obj.create(self.cursor, self.uid, {
                "name": "Àngel és una categoria invàlida",
            })
