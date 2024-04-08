from tests_gurb_base import TestsGurbBase


class TestsGurbCups(TestsGurbBase):

    def test_gurb_cups_percentage(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")

        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]
        percentatge_1 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_1, ['beta_percentage']
        )['beta_percentage']
        percentatge_2 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_2, ['beta_percentage']
        )['beta_percentage']

        self.assertEqual(percentatge_1, 35.0)
        self.assertEqual(percentatge_2, 30.0)
