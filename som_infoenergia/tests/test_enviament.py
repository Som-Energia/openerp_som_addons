# -*- coding: utf-8 -*-
from destral import testing
import unittest
from destral.transaction import Transaction


import mock


class EnviamentTests(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Pending refactor to remove empowering_profile_id from polissa")
    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_not_emp_allow_recieve_mail_infoenergia(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        pol_id = enviament.polissa_id.id

        pol_obj.write(
            cursor, uid, pol_id, {"data_baixa": False, "emp_allow_recieve_mail_infoenergia": False}
        )
        enviament.send_single_report()

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "cancellat")
        mocked_send_mail.assert_not_called()

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_without_attachment(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        pol_id = enviament.polissa_id.id

        pol_obj.write(cursor, uid, pol_id, {"data_baixa": False})
        enviament.send_single_report()

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "error")
        mocked_send_mail.assert_not_called()

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_polissa_data_baixa(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert_amb_attach"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        pol_id = enviament.polissa_id.id

        pol_obj.write(cursor, uid, pol_id, {"data_baixa": "2020-01-01"})
        enviament.send_single_report()

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "baixa")
        mocked_send_mail.assert_not_called()

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_polissa_inactiva(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert_amb_attach"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        pol_id = enviament.polissa_id.id

        pol_obj.write(cursor, uid, pol_id, {"active": False})
        enviament.send_single_report()

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "baixa")
        mocked_send_mail.assert_not_called()

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_enviat(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert_amb_attach"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        enviament.write({"estat": "enviat"})

        pol_id = enviament.polissa_id.id

        pol_obj.write(cursor, uid, pol_id, {"data_baixa": False})
        enviament.send_single_report()

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "enviat")
        mocked_send_mail.assert_not_called()

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_allow_reenviar(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert_amb_attach"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        enviament.write({"estat": "enviat"})

        pol_id = enviament.polissa_id.id

        pol_obj.write(cursor, uid, pol_id, {"data_baixa": False})
        enviament.send_single_report(context={"allow_reenviar": True})

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "enviat")
        mocked_send_mail.assert_called_with(
            context={
                "src_model": "som.infoenergia.enviament",
                "src_rec_ids": [enviament_id],
                "allow_reenviar": True,
                "template_id": enviament.lot_enviament.email_template.id,
                "active_id": enviament_id,
            }
        )

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_ok(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert_amb_attach"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        pol_id = enviament.polissa_id.id

        pol_obj.write(cursor, uid, pol_id, {"data_baixa": False})
        enviament.send_single_report()

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "obert")
        mocked_send_mail.assert_called_with(
            context={
                "src_model": "som.infoenergia.enviament",
                "src_rec_ids": [enviament_id],
                "template_id": enviament.lot_enviament.email_template.id,
                "active_id": enviament_id,
            }
        )

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_single_report_email_subject_context(self, mocked_send_mail):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cursor = self.cursor
        uid = self.uid

        enviament_id = imd_obj.get_object_reference(
            cursor, uid, "som_infoenergia", "enviament_obert_amb_attach"
        )[1]
        enviament = env_obj.browse(cursor, uid, enviament_id)

        pol_id = enviament.polissa_id.id

        pol_obj.write(cursor, uid, pol_id, {"data_baixa": False})
        ctx = {"email_subject": "Test subject", "email_to": "test@test.test"}
        enviament.send_single_report(context=ctx)

        self.assertEqual(env_obj.read(cursor, uid, enviament_id, ["estat"])["estat"], "obert")
        mocked_send_mail.assert_called_with(
            context={
                "src_model": "som.infoenergia.enviament",
                "src_rec_ids": [enviament_id],
                "template_id": enviament.lot_enviament.email_template.id,
                "email_to": "test@test.test",
                "email_subject": "Test subject",
                "active_id": enviament_id,
            }
        )

    def test_add_info_line__single_env_infoenergia(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_infoenergia", "enviament_obert_amb_attach"
        )[1]
        enviament = env_obj.browse(self.cursor, self.uid, enviament_id)
        info_pre = enviament.info

        enviament.add_info_line(u"Test add info line")

        info_post = env_obj.read(self.cursor, self.uid, enviament_id, ["info"])["info"]
        self.assertTrue(u"Test add info line\n{}".format(info_pre) in info_post)

    def test_add_info_line__two_env_infoenergia(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.infoenergia.enviament")
        enviaments = []
        enviaments.append(
            imd_obj.get_object_reference(
                self.cursor, self.uid, "som_infoenergia", "enviament_obert_amb_attach"
            )[1]
        )
        enviaments.append(
            imd_obj.get_object_reference(
                self.cursor, self.uid, "som_infoenergia", "enviament_obert"
            )[1]
        )
        info_pre_0 = env_obj.read(self.cursor, self.uid, enviaments[0], ["info"])["info"]
        info_pre_1 = env_obj.read(self.cursor, self.uid, enviaments[1], ["info"])["info"]

        env_obj.add_info_line(self.cursor, self.uid, enviaments, u"Test add info line")

        info_post_0 = env_obj.read(self.cursor, self.uid, enviaments[0], ["info"])["info"]
        info_post_1 = env_obj.read(self.cursor, self.uid, enviaments[1], ["info"])["info"]
        self.assertTrue(u"Test add info line\n{}".format(info_pre_0) in info_post_0)
        self.assertTrue(u"Test add info line\n{}".format(info_pre_1) in info_post_1)

    def test_add_info_line__single_env_massiu(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.enviament.massiu")
        enviament_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_infoenergia", "enviament_obert_tipus_altre"
        )[1]
        enviament = env_obj.browse(self.cursor, self.uid, enviament_id)
        info_pre = enviament.info

        enviament.add_info_line(u"Test add info line")

        info_post = env_obj.read(self.cursor, self.uid, enviament_id, ["info"])["info"]
        self.assertTrue(u"Test add info line\n{}".format(info_pre) in info_post)

    def test_add_info_line__two_env_massiu(self):
        imd_obj = self.openerp.pool.get("ir.model.data")
        env_obj = self.openerp.pool.get("som.enviament.massiu")
        enviaments = []
        enviaments.append(
            imd_obj.get_object_reference(
                self.cursor, self.uid, "som_infoenergia", "enviament_obert_tipus_altre"
            )[1]
        )
        enviaments.append(
            imd_obj.get_object_reference(
                self.cursor, self.uid, "som_infoenergia", "enviament_enviat_tipus_altre"
            )[1]
        )
        info_pre_0 = env_obj.read(self.cursor, self.uid, enviaments[0], ["info"])["info"]
        info_pre_1 = env_obj.read(self.cursor, self.uid, enviaments[1], ["info"])["info"]

        env_obj.add_info_line(self.cursor, self.uid, enviaments, u"Test add info line")

        info_post_0 = env_obj.read(self.cursor, self.uid, enviaments[0], ["info"])["info"]
        info_post_1 = env_obj.read(self.cursor, self.uid, enviaments[1], ["info"])["info"]
        self.assertTrue(u"Test add info line\n{}".format(info_pre_0) in info_post_0)
        self.assertTrue(u"Test add info line\n{}".format(info_pre_1) in info_post_1)
