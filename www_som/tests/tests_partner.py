# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction


class TestPartnerWww(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        return self.imd_obj.get_object_reference(
            self.cursor, self.uid, model, reference)[1]

    def setUp(self):
        self.imd_obj = self.model("ir.model.data")
        self.parnter_obj = self.model("res.partner")

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_www_ov_attachments(self):
        partner_id = self.get_fixture("base", "res_partner_asus")
        expected_attachment_1 = self.get_fixture(
            "www_som", "ov_attachment_partner_asus")
        expected_attachment_2 = self.get_fixture(
            "www_som", "ov_attachment_mail_partner_asus_ov")

        ov_attachments = self.parnter_obj.www_ov_attachments(
            self.cursor, self.uid, partner_id)
        ov_attachments_ids = [a["erp_id"] for a in ov_attachments]

        self.assertItemsEqual(
            ov_attachments_ids, [expected_attachment_1, expected_attachment_2])
