# -*- coding: utf-8 -*-
import json
from destral import testing
from osv.orm import FieldsValidationException


class TestPoweremail(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.category_obj = self.openerp.pool.get("poweremail.sendgrid.category")
        self.template_obj = self.openerp.pool.get("poweremail.templates")
        self.mail_obj = self.openerp.pool.get("poweremail.mailbox")
        self.poweremail_core_obj = self.openerp.pool.get("poweremail.core_accounts")
        super(TestPoweremail, self).setUp()

    def test_category_name_validation(self):
        # With ascii, it don't fail
        self.category_obj.create(self.cursor, self.uid, {
            "name": "Canvi de preus",
        })

        # With special characters, it fails
        with self.assertRaises(FieldsValidationException):
            self.category_obj.create(self.cursor, self.uid, {
                "name": "Àngel és una categoria invàlida",
            })

    def test_add_sendgrid_category_headers_to_context(self):
        cat_a_id = self.category_obj.create(self.cursor, self.uid, {
            "name": "A",
        })
        cat_b_id = self.category_obj.create(self.cursor, self.uid, {
            "name": "B",
        })

        template_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "poweremail", "default_template_poweremail")[1]
        self.template_obj.write(
            self.cursor, self.uid, template_id, {
                "sendgrid_category_ids": [(6, 0, [cat_a_id, cat_b_id])],
                "enforce_from_account": 1,
            },
        )

        mail_id = self.template_obj.generate_mail(self.cursor, self.uid, template_id, 1)

        context = {'some': 'thing'}
        context = self.poweremail_core_obj.add_sendgrid_category_headers_to_context(
            self.cursor, self.uid, mail_id, context)
        self.assertEqual(context['headers']['X-SMTPAPI'], json.dumps({
            'category': ['A', 'B']
        }))
        self.assertEqual(context['some'], 'thing')
