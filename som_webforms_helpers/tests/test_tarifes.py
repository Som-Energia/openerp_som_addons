# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class tarifes_tests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get("ir.model.data")

    def tearDown(self):
        pass

    def test__dummyTest(self):
        self.assertTrue(True)

    def test__get_tariff_prices_valid_date(self):
        """
        Checks that given a tariff and a date there are prices in that date
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            model = self.pool.get("giscedata.polissa.tarifa")
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "tarifa_20A_test"
            )[1]

            result = model.get_tariff_prices(
                cursor, uid, tariff_id, 5386, None, False, "2021-12-01"
            )
            self.assertTrue(result)

    def test__get_tariff_prices_invalid_date(self):
        """
        Checks that given a tariff and a date there are not prices in that date
        :return: warning.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            model = self.pool.get("giscedata.polissa.tarifa")
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "tarifa_20A_test"
            )[1]

            with self.assertRaises(Exception) as e:
                model.get_tariff_prices(
                    cursor, uid, tariff_id, 5386, None, False, "1999-12-01"
                )

            self.assertEqual(e.exception.value, "Tariff pricelist not found")
