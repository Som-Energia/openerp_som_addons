from tests_gurb_base import TestsGurbBase


class TestsGurbWWW(TestsGurbBase):

    def test__get_open_gurb__one_opened(self):
        gurb_www_obj = self.get_model("som.gurb.www")

        open_gurbs = gurb_www_obj.get_open_gurbs(self.cursor, self.uid)

        self.assertEqual(open_gurbs[0]['name'], 'GURB 001')

    def test__get_open_gurb__none_opened(self):
        gurb_obj = self.get_model("som.gurb")
        gurb_www_obj = self.get_model("som.gurb.www")

        gurb_id = self.get_references()['gurb_0001']
        gurb_obj.write(self.cursor, self.uid, gurb_id, {'state': 'active'})
        open_gurbs = gurb_www_obj.get_open_gurbs(self.cursor, self.uid)

        self.assertEqual(open_gurbs, [])

    def test__check_cups_2km_validation__inside2km(self):
        gurb_www_obj = self.get_model("som.gurb.www")
        cups_obj = self.get_model("giscedata.cups.ps")

        gurb_id = self.get_references()['gurb_0001']
        cups_id = self.get_references()['cups_id_2']
        cups = cups_obj.read(self.cursor, self.uid, cups_id, ['name'])['name']
        result = gurb_www_obj.check_cups_2km_validation(self.cursor, self.uid, cups, gurb_id)

        self.assertTrue(result)

    def test__check_cups_2km_validation__outside2km(self):
        gurb_www_obj = self.get_model("som.gurb.www")
        cups_obj = self.get_model("giscedata.cups.ps")

        gurb_id = self.get_references()['gurb_0001']
        cups_id = self.get_references()['cups_id']
        cups = cups_obj.read(self.cursor, self.uid, cups_id, ['name'])['name']
        result = gurb_www_obj.check_cups_2km_validation(self.cursor, self.uid, cups, gurb_id)

        self.assertFalse(result)

    def test__check_coordinates_2km_validation__inside2km(self):
        gurb_www_obj = self.get_model("som.gurb.www")

        gurb_id = self.get_references()['gurb_0001']
        result = gurb_www_obj.check_coordinates_2km_validation(
            self.cursor, self.uid, -3.064674264239092, 37.35812464702857, gurb_id
        )

        self.assertTrue(result)

    def test__check_coordinates_2km_validation__outside2km(self):
        gurb_www_obj = self.get_model("som.gurb.www")

        gurb_id = self.get_references()['gurb_0001']
        result = gurb_www_obj.check_coordinates_2km_validation(
            self.cursor, self.uid, 37.35812464702857, -3.064674264239092, gurb_id
        )

        self.assertFalse(result)
