# -*- coding: utf-8 -*-
from tests_gurb_base import TestsGurbBase


class TestsGurbWww(TestsGurbBase):

    def test_get_info_gurb__bad_gurb_code(self):
        gurb_www_o = self.openerp.pool.get("som.gurb.www")

        bad_gurb_name = "erroneus_code"
        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            bad_gurb_name,
            "2.0TD"
        )

        msg = u"Cap Gurb Group amb el codi {}".format(bad_gurb_name)
        self.assertEqual(result["error"], msg)
        self.assertEqual(result["code"], "BadGurbCode")

    def test_get_info_gurb__unsuported_access_tariff(self):
        gurb_www_o = self.openerp.pool.get("som.gurb.www")

        bad_access_tariff = "6.1TD"
        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            bad_access_tariff
        )

        msg = u"Tarifa d'accés no suportada '{}'".format(bad_access_tariff)
        self.assertEqual(result["error"], msg)
        self.assertEqual(result["code"], "UnsuportedAccessTariff")

    def test_get_info_gurb__available_betas(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_www_o = self.openerp.pool.get("som.gurb.www")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")

        # GURB CUPS must be active
        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]
        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_1, {"state": "active"})
        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_2, {"state": "active"})

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "2.0TD"
        )

        self.assertEqual(result["available_betas"], [x / 10.0 for x in range(5, 25, 5)])

    def test_get_info_gurb__surplus_comensation(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_www_o = self.openerp.pool.get("som.gurb.www")
        gurb_cau_o = self.openerp.pool.get("som.gurb.cau")

        gurb_cau_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cau_0001"
        )[1]
        gurb_cau_o.write(self.cursor, self.uid, gurb_cau_id, {"has_compensation": True})

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "2.0TD"
        )

        self.assertTrue(result["surplus_compensation"])

    def test_get_info_gurb__quotas(self):
        gurb_www_o = self.openerp.pool.get("som.gurb.www")

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "2.0TD"
        )

        self.assertEqual(result["initial_quota"], 3.75)
        self.assertEqual(result["quota"], 5)

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "3.0TD"
        )
        self.assertEqual(result["quota"], 4)
