from tests_gurb_base import TestsGurbBase
from osv import osv
from datetime import datetime, timedelta


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

    def test_gurb_is_owner(self):

        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")

        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]
        owner_cups_1 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_1, ["owner_cups"]
        )["owner_cups"]
        owner_cups_2 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_2, ["owner_cups"]
        )["owner_cups"]

        self.assertEqual(owner_cups_1, True)
        self.assertEqual(owner_cups_2, False)

    def test_wizard_gurb_create_new_beta(self):
        context = {}

        gurb_cups_id = self.get_references()['gurb_cups_id']
        start_date = "2015-02-01"
        new_beta_kw = 1.5
        new_extra_beta_kw = 0.5

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, context=context
            )

        new_beta_kw = -10

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, context=context
            )

        new_beta_kw = 0
        new_extra_beta_kw = 0

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, context=context
            )

        start_date = (datetime.today() + timedelta(days=20)).strftime("%Y-%m-%d")
        new_beta_kw = 1.5
        new_extra_beta_kw = 0.5

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, context=context
            )

        new_beta_kw = 2.5
        new_extra_beta_kw = 1
        start_date = "2017-02-01"

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, context=context
            )

        new_beta_kw = 3
        new_extra_beta_kw = 2
        start_date = (datetime.today()).strftime("%Y-%m-%d")

        self.create_new_gurb_cups_beta(
            gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, context=context
        )
