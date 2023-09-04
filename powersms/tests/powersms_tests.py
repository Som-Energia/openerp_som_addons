# -*- coding: utf-8 -*-
import unittest
import mock
from destral import testing
from destral.transaction import Transaction


class powersms_tests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get("ir.model.data")

    def tearDown(self):
        pass

    def test__dummyTest(self):
        self.assertTrue(True)

    @mock.patch("sql_db.Cursor.commit")
    @mock.patch("powersms.powersms_smsbox.PowersmsSMSbox.async_send_this_sms")
    def test__powersms_run_sms_scheduler__ok(self, mocked_send, mock_commit):
        """
        Checks if run_sms_shceduler is calling async send sms function
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            psb = self.openerp.pool.get("powersms.smsbox")
            nsms_outbox_pre = psb.search(cursor, uid, [("folder", "=", "outbox")])
            nsms_sent_pre = psb.search(cursor, uid, [("folder", "=", "sent")])

            psb.run_sms_scheduler(cursor, uid, {})

            mock_commit.assert_called_with()
            mocked_send.assert_called_with(cursor, uid, nsms_outbox_pre, {})

    def test__powersms_historise__ok(self):
        """
        Checks if SMS history is updated
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            psb = self.pool.get("powersms.smsbox")
            sms_id = self.imd_obj.get_object_reference(cursor, uid, "powersms", "sms_outbox_001")[1]

            response = psb.historise(cursor, uid, [sms_id], u"SMS sent successfully")

            history = psb.read(cursor, uid, sms_id, ["history"])
            self.assertTrue(u"SMS sent successfully" in history["history"])


class powersms_send_wizard_tests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get("ir.model.data")
        self.wiz_obj = self.pool.get("powersms.send.wizard")

    def tearDown(self):
        pass

    def test__powersms_send_wizard__save_to_smsbox(self):
        """
        Checks if sms is created with save_to_smsbox function
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.pool.get("powersms.send.wizard")
            temp_id = self.imd_obj.get_object_reference(
                cursor, uid, "powersms", "sms_template_001"
            )[1]
            rpa_id = self.imd_obj.get_object_reference(
                cursor, uid, "base", "res_partner_address_c2c_1"
            )[1]
            pca_id = self.imd_obj.get_object_reference(cursor, uid, "powersms", "sms_account_001")[
                1
            ]
            vals = {"account": pca_id, "body_text": "Test text"}
            context = {
                "template_id": temp_id,
                "rel_model": "res_partner_address",
                "src_rec_ids": [rpa_id],
                "active_id": rpa_id,
                "active_ids": [rpa_id],
                "src_model": "res.partner.address",
                "from": "Som Energia",
                "account": pca_id,
            }

            wizard_id = model.create(cursor, uid, vals, context)
            model.write(cursor, uid, [wizard_id], {"to": 666666666})
            wizard_load_n = model.browse(cursor, uid, wizard_id)
            sms_created_id = wizard_load_n.save_to_smsbox(context)

            psb = self.openerp.pool.get("powersms.smsbox")

            sms_id = psb.search(
                cursor,
                uid,
                [
                    ("id", "=", sms_created_id),
                    ("psms_body_text", "=", "Test text"),
                    ("folder", "=", "outbox"),
                ],
            )
            self.assertTrue(sms_created_id[0] in sms_id)

    def test__powersms_send_wizard__send_sms_isNotValid(self):
        """
        Checks if when 'to' is not a valid number, the sms is created in drafts
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.pool.get("powersms.send.wizard")
            temp_id = self.imd_obj.get_object_reference(
                cursor, uid, "powersms", "sms_template_001"
            )[1]
            rpa_id = self.imd_obj.get_object_reference(
                cursor, uid, "base", "res_partner_address_c2c_1"
            )[1]
            pca_id = self.imd_obj.get_object_reference(cursor, uid, "powersms", "sms_account_001")[
                1
            ]
            vals = {"account": pca_id, "body_text": "Test sms in draft folder", "to": "notANumber"}
            context = {
                "template_id": temp_id,
                "rel_model": "res_partner_address",
                "src_rec_ids": [rpa_id],
                "active_id": rpa_id,
                "active_ids": [rpa_id],
                "src_model": "res.partner.address",
                "from": "Som Energia",
                "account": pca_id,
            }

            wizard_id = model.create(cursor, uid, vals, context)
            wizard_load_n = model.browse(cursor, uid, wizard_id)
            wizard_load_n.send_sms(context)

            psb = self.openerp.pool.get("powersms.smsbox")
            sms_id = psb.search(
                cursor,
                uid,
                [("psms_body_text", "=", "Test sms in draft folder"), ("folder", "=", "drafts")],
            )
            self.assertTrue(sms_id)

    def test__powersm_send_wizard_save_to_smsbox__empty_numbers(self):
        """
        Checks if when create_empty_number = False, and 'to' is empty, the sms is not created
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.pool.get("powersms.send.wizard")
            temp_id = self.imd_obj.get_object_reference(
                cursor, uid, "powersms", "sms_template_001"
            )[1]
            rpa_id = self.imd_obj.get_object_reference(
                cursor, uid, "base", "res_partner_address_c2c_1"
            )[1]
            pca_id = self.imd_obj.get_object_reference(cursor, uid, "powersms", "sms_account_001")[
                1
            ]
            vals = {"account": pca_id, "body_text": "Test text", "to": ""}
            context = {
                "template_id": temp_id,
                "rel_model": "res_partner_address",
                "src_rec_ids": [rpa_id],
                "active_id": rpa_id,
                "active_ids": [rpa_id],
                "src_model": "res.partner.address",
                "from": "Som Energia",
                "account": pca_id,
                "create_empty_number": False,
            }

            wizard_id = model.create(cursor, uid, vals, context)
            wizard_load_n = model.browse(cursor, uid, wizard_id)
            sms_created_id = wizard_load_n.save_to_smsbox(context)

            self.assertFalse(sms_created_id)

    def test__powersm_send_wizard_save_to_smsbox__empty_numbers_allowed(self):
        """
        Checks if when create_empty_number = True, and 'to' is empty, the sms is created
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.pool.get("powersms.send.wizard")
            temp_id = self.imd_obj.get_object_reference(
                cursor, uid, "powersms", "sms_template_001"
            )[1]
            rpa_id = self.imd_obj.get_object_reference(
                cursor, uid, "base", "res_partner_address_c2c_1"
            )[1]
            pca_id = self.imd_obj.get_object_reference(cursor, uid, "powersms", "sms_account_001")[
                1
            ]
            vals = {"account": pca_id, "body_text": "Test text", "to": ""}
            context = {
                "template_id": temp_id,
                "rel_model": "res_partner_address",
                "src_rec_ids": [rpa_id],
                "active_id": rpa_id,
                "active_ids": [rpa_id],
                "src_model": "res.partner.address",
                "from": "Som Energia",
                "account": pca_id,
                "create_empty_number": True,
            }

            wizard_id = model.create(cursor, uid, vals, context)
            wizard_load_n = model.browse(cursor, uid, wizard_id)
            sms_created_id = wizard_load_n.save_to_smsbox(context)

            psb = self.openerp.pool.get("powersms.smsbox")
            sms_id = psb.search(
                cursor,
                uid,
                [
                    ("id", "=", sms_created_id),
                    ("psms_body_text", "=", "Test text"),
                    ("folder", "=", "outbox"),
                ],
            )
            self.assertTrue(sms_created_id[0] in sms_id)
