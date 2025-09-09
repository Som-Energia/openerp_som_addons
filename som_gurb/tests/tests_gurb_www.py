# -*- coding: utf-8 -*-
from tests_gurb_base import TestsGurbBase


class TestsGurbWww(TestsGurbBase):

    def test_get_info_gurb__bad_gurb_code(self):
        gurb_www_o = self.openerp.pool.get("som.gurb.www")

        bad_gurb_name = "gurb_group_0001_erroni"
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
            'gurb_group_0001',
            bad_access_tariff
        )

        msg = u"Tarifa d'accés no suportada '{}'".format(bad_access_tariff)
        self.assertEqual(result["error"], msg)
        self.assertEqual(result["code"], "UnsuportedAccessTariff")
