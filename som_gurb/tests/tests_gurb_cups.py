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
        self.assertEqual(percentatge_2, 35.0)

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

        gurb_cups_beta_o = self.openerp.pool.get("som.gurb.cups.beta")

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
        gurb_cups_beta_id = gurb_cups_beta_o.search(
            self.cursor, self.uid, [("gurb_cups_id", "=", gurb_cups_id), ("future_beta", "=", True)]
        )
        self.assertEqual(len(gurb_cups_beta_id), 1)

    def test_gurb_cups_activation(self):
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        gurb_cups_beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        pol_o = self.openerp.pool.get("giscedata.polissa")

        gurb_cups_id = self.get_references()["gurb_cups_id"]
        gurb_cups_beta_id = self.get_references()["gurb_cups_beta_2_id"]

        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id, {"start_date": False})
        gurb_cups_beta_o.write(self.cursor, self.uid, gurb_cups_beta_id, {"future_beta": True})
        gurb_cups_o.activate_or_modify_gurb_cups(self.cursor, self.uid, gurb_cups_id, "2024-01-01")

        pol_id = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id, ["polissa_id"]
        )["polissa_id"][0]
        pol_br = pol_o.browse(self.cursor, self.uid, pol_id)
        gurb_cups_br = gurb_cups_o.browse(self.cursor, self.uid, gurb_cups_id)
        gurb_cups_beta_br = gurb_cups_beta_o.browse(self.cursor, self.uid, gurb_cups_id)

        self.assertEqual(len(pol_br.serveis), 1)
        self.assertEqual(pol_br.serveis[0].polissa_id.id, pol_id)
        self.assertEqual(gurb_cups_br.start_date, "2024-01-01")
        self.assertEqual(gurb_cups_beta_br.future_beta, False)
