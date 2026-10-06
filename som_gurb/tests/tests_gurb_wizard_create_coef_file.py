# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from tests_gurb_base import TestsGurbBase


class TestsGurbWizardCreateCoefFile(TestsGurbBase):

    def test_gurb_wizard_creacte_coef_file(self):

        self.activate_gurb_cups()

        ctx = {
            "active_id": self.get_references()["gurb_cau_id"]
        }

        wiz_obj = self.openerp.pool.get("wizard.create.coeficients.file")
        wiz_id = wiz_obj.create(self.cursor, self.uid, {}, context=ctx)
        wiz_obj.create_coeficients_file_txt(self.cursor, self.uid, [wiz_id], context=ctx)

        file = wiz_obj.read(
            self.cursor, self.uid, wiz_id, ['file'], context=ctx
        )[0]['file']

        decoded_file = base64.b64decode(file)

        self.assertEqual(
            decoded_file, "ES1234000000000001JN0F;0,350000"
        )

    def test_gurb_wizard_creacte_coef_file_with_future_beta(self):

        self.activate_gurb_cups()

        ctx = {
            "active_id": self.get_references()["gurb_cau_id"]
        }

        gurb_cups_id = self.get_references()['gurb_cups_id']
        start_date = (datetime.now()).strftime("%Y-%m-%d")
        new_beta_kw = 0.5
        new_extra_beta_kw = 0
        gift_beta_kw = 0
        self.create_new_gurb_cups_beta(
            gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, gift_beta_kw
        )

        wiz_obj = self.openerp.pool.get("wizard.create.coeficients.file")
        wiz_id = wiz_obj.create(self.cursor, self.uid, {}, context=ctx)
        wiz_obj.create_coeficients_file_txt(self.cursor, self.uid, [wiz_id], context=ctx)

        file = wiz_obj.read(
            self.cursor, self.uid, wiz_id, ['file'], context=ctx
        )[0]['file']

        decoded_file = base64.b64decode(file)

        self.assertEqual(
            decoded_file, "ES1234000000000001JN0F;0,350000\r\nES0021126262693495FV;0,050000"
        )

    def test_coef_file_sum_precision(self):
        """3 CUPS with equal betas (1/3 of generation power each) should sum to 1.000000"""
        imd_obj = self.openerp.pool.get("ir.model.data")
        gurb_cau_obj = self.openerp.pool.get("som.gurb.cau")
        gurb_cups_obj = self.openerp.pool.get("som.gurb.cups")
        gurb_cups_beta_obj = self.openerp.pool.get("som.gurb.cups.beta")
        cups_ps_obj = self.openerp.pool.get("giscedata.cups.ps")
        wiz_obj = self.openerp.pool.get("wizard.create.coeficients.file")

        refs = self.get_references()
        gurb_cau_id = refs["gurb_cau_id"]
        cups_0001_id = refs["owner_gurb_cups_id"]
        cups_0002_id = refs["gurb_cups_id"]

        # generation_power=9, beta=3 per CUPS → coef = 3/9 = 0.333333... (repeating)
        # 3 CUPS × 0.333333 = 0.999999 (float precision bug)
        gurb_cau_obj.write(
            self.cursor, self.uid, gurb_cau_id, {"generation_power": 9.0}
        )

        # Activate cups_0001 and cups_0002 via workflow
        gurb_cups_obj.send_signal(
            self.cursor, self.uid, [cups_0001_id, cups_0002_id], "button_create_cups"
        )
        gurb_cups_obj.send_signal(
            self.cursor, self.uid, [cups_0001_id, cups_0002_id], "button_activate_cups"
        )

        # Create a 3rd CUPS PS and gurb_cups
        id_municipi = imd_obj.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_01001"
        )[1]
        config_obj = self.openerp.pool.get("res.config")
        config_obj.set(self.cursor, self.uid, 'check_cups', 0)
        cups_ps_03_id = cups_ps_obj.create(self.cursor, self.uid, {
            "name": "ES9999999999999901XX",
            "id_municipi": id_municipi,
        })
        config_obj.set(self.cursor, self.uid, 'check_cups', 1)
        cups_0003_id = gurb_cups_obj.create(self.cursor, self.uid, {
            "inscription_date": "2016-01-01",
            "start_date": "2016-01-01",
            "gurb_cau_id": gurb_cau_id,
            "cups_id": cups_ps_03_id,
            "active": True,
        })
        gurb_cups_obj.send_signal(
            self.cursor, self.uid, [cups_0003_id], "button_create_cups"
        )
        gurb_cups_obj.send_signal(
            self.cursor, self.uid, [cups_0003_id], "button_activate_cups"
        )

        # Set future beta = 3.0 kW for all 3 CUPS
        # _ff_get_future_beta_percentage picks these up → 3*100/9 = 33.333...%
        today = datetime.today().strftime('%Y-%m-%d')
        for cups_id in [cups_0001_id, cups_0002_id, cups_0003_id]:
            gurb_cups_beta_obj.create(self.cursor, self.uid, {
                "active": True,
                "start_date": today,
                "future_beta": True,
                "beta_kw": 3.0,
                "extra_beta_kw": 0.0,
                "gift_beta_kw": 0.0,
                "gurb_cups_id": cups_id,
            })

        ctx = {"active_id": gurb_cau_id}
        items = wiz_obj.get_items(self.cursor, self.uid, today, context=ctx)

        self.assertEqual(len(items), 3)
        coefs = [float(item["coef"].replace(",", ".")) for item in items]
        total = sum(coefs)
        self.assertEqual("{:1,.6f}".format(total), "1.000000")
