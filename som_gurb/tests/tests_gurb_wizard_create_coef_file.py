import base64
from datetime import datetime
from tests_gurb_base import TestsGurbBase


class TestsGurbWizardCreateCoefFile(TestsGurbBase):

    def test_gurb_wizard_creacte_coef_file(self):

        ctx = {
            "active_id": self.get_references()["gurb_id"]
        }

        wiz_obj = self.openerp.pool.get("wizard.create.coeficients.file")
        wiz_id = wiz_obj.create(self.cursor, self.uid, {}, context=ctx)
        wiz_obj.create_coeficients_file_txt(self.cursor, self.uid, [wiz_id], context=ctx)

        file = wiz_obj.read(
            self.cursor, self.uid, wiz_id, ['file'], context=ctx
        )[0]['file']

        decoded_file = base64.b64decode(file)

        self.assertEqual(
            decoded_file, "ES1234000000000001JN0F;0,350000\r\nES0021126262693495FV;0,350000"
        )

    def test_gurb_wizard_creacte_coef_file_with_future_beta(self):

        ctx = {
            "active_id": self.get_references()["gurb_id"]
        }

        gurb_cups_id = self.get_references()['gurb_cups_id']
        start_date = (datetime.now()).strftime("%Y-%m-%d")
        new_beta_kw = 0.5
        new_extra_beta_kw = 0
        self.create_new_gurb_cups_beta(
            gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw
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
