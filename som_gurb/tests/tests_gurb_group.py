from tests_gurb_base import TestsGurbBase


class TestsGurbGroup(TestsGurbBase):

    def test_gurb_group_gift_betas(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        gurb_group_o = self.openerp.pool.get("som.gurb.group")
        gurb_cups_beta_o = self.openerp.pool.get("som.gurb.cups.beta")

        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]

        gurb_beta_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_beta_0001"
        )[1]
        gurb_beta_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_beta_0002"
        )[1]

        gurb_group_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_group_0001"
        )[1]

        gurb_cups_beta_o.write(
            self.cursor, self.uid, gurb_beta_id_1, {"gift_beta_kw": 0.5})
        gurb_cups_beta_o.write(
            self.cursor, self.uid, gurb_beta_id_2, {"gift_beta_kw": 0.5})
        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_1, {"start_date": False})
        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_2, {"start_date": False})

        gurb_cups_o.send_signal(self.cursor, self.uid, [gurb_cups_id_1], "button_create_cups")
        gurb_cups_o.send_signal(self.cursor, self.uid, [gurb_cups_id_2], "button_create_cups")

        gurb_cups_o.activate_or_modify_gurb_cups(
            self.cursor, self.uid, gurb_cups_id_1, "2024-01-01")
        gurb_cups_o.activate_or_modify_gurb_cups(
            self.cursor, self.uid, gurb_cups_id_2, "2024-01-01")

        gift_betas_kw = gurb_group_o.read(
            self.cursor, self.uid, gurb_group_id_1, ['gift_betas_kw']
        )['gift_betas_kw']

        self.assertEqual(gift_betas_kw, 1)

    def test_gurb_group_extra_betas(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        gurb_group_o = self.openerp.pool.get("som.gurb.group")

        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]

        gurb_group_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_group_0001"
        )[1]

        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_1, {"start_date": False})
        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_2, {"start_date": False})

        gurb_cups_o.send_signal(self.cursor, self.uid, [gurb_cups_id_1], "button_create_cups")
        gurb_cups_o.send_signal(self.cursor, self.uid, [gurb_cups_id_2], "button_create_cups")

        gurb_cups_o.activate_or_modify_gurb_cups(
            self.cursor, self.uid, gurb_cups_id_1, "2024-01-01")
        gurb_cups_o.activate_or_modify_gurb_cups(
            self.cursor, self.uid, gurb_cups_id_2, "2024-01-01")

        extra_betas_kw = gurb_group_o.read(
            self.cursor, self.uid, gurb_group_id_1, ['extra_betas_kw']
        )['extra_betas_kw']
        extra_betas_percentage = gurb_group_o.read(
            self.cursor, self.uid, gurb_group_id_1, ['extra_betas_percentage']
        )['extra_betas_percentage']

        self.assertEqual(extra_betas_kw, 2)
        self.assertEqual(extra_betas_percentage, 20)

    def test_gurb_group_get_prioritary_gurb_cau_id(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_group_o = self.openerp.pool.get("som.gurb.group")
        gurb_group_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_group_0001"
        )[1]
        gurb_cau_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cau_0001"
        )[1]

        gurb_cau_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cau_0002"
        )[1]

        beta_5 = gurb_group_o.get_prioritary_gurb_cau_id(self.cursor, self.uid, gurb_group_id_1, 5)
        self.assertEqual(beta_5, gurb_cau_id_1)
        beta_15 = gurb_group_o.get_prioritary_gurb_cau_id(
            self.cursor, self.uid, gurb_group_id_1, 15
        )
        self.assertEqual(beta_15, gurb_cau_id_2)
