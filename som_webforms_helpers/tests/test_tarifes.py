# -*- coding: utf-8 -*-
from destral import testing
import unittest
from destral.transaction import Transaction

class tarifes_tests(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get('ir.model.data')

    def tearDown(self):
        pass

    def test__dummyTest(self):
        self.assertTrue(True)

    def test__get_tariff_prices__valid_date(self):
        """
        Checks that given a tariff and a date there are prices in that date
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.pool.get('giscedata.polissa.tarifa')
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, 'giscedata_polissa', 'tarifa_20A_test')[1]
            result = model.get_tariff_prices(cursor, uid, tariff_id, 5386, 15000, None, False, '2021-12-01', '2021-12-01')
            self.assertTrue(result)

    def test__get_tariff_prices__invalid_date(self):
        """
        Checks that given a tariff and a date there are not prices in that date
        :return: warning.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            model = self.pool.get('giscedata.polissa.tarifa')
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, 'giscedata_polissa', 'tarifa_20A_test')[1]

            with self.assertRaises(Exception) as e:
                model.get_tariff_prices(cursor, uid, tariff_id, 5386, None, False, '1999-12-01', '1999-12-01')

            self.assertEqual(e.exception.value, 'Tariff pricelist not found')

    def test__get_tariff_prices__valid_date_range_date_tariff_into_range(self):

        date_start = '2022-12-01'
        date_end = '2023-01-31'

        date_from = '2021-01-01'
        date_to = '2023-02-01'

        self.assertTrue((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__valid_date_range_date_from_into_tariff(self):

        date_start = '2022-12-01'
        date_end = '2023-01-31'

        date_from = '2022-12-15'
        date_to = '2023-02-01'

        self.assertTrue((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__valid_date_range_date_to_into_tariff(self):

        date_start = '2022-12-01'
        date_end = '2023-01-31'

        date_from = '2021-01-01'
        date_to = '2023-01-15'

        self.assertTrue((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__valid_date_range_date_range_into_tariff(self):

        date_start = '2022-12-01'
        date_end = '2023-01-31'

        date_from = '2021-12-15'
        date_to = '2023-01-15'

        self.assertTrue((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__valid_date_range_date_range_equal_tariff_range(self):

        date_start = '2022-12-01'
        date_end = '2023-01-31'

        date_from = '2021-12-01'
        date_to = '2023-01-31'

        self.assertTrue((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__valid_date_range_date_range_before_tariff_range(self):

        date_start = '2022-12-01'
        date_end = '2023-01-31'

        date_from = '2020-12-01'
        date_to = '2022-01-31'

        self.assertFalse((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__valid_date_range_date_range_after_tariff_range(self):

        date_start = '2022-12-01'
        date_end = '2023-01-31'

        date_from = '2023-12-01'
        date_to = '2024-01-31'

        self.assertFalse((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__valid_date_range_with_active_tariff(self):

        date_start = '2022-12-01'
        date_end = False

        date_from = '2022-12-15'
        date_to = '2024-01-31'

        self.assertTrue((not date_end or date_from <= date_end) and (not date_start or date_to >= date_start))

    def test__get_tariff_prices__without_dates(self):
        """
        Get an active tariff
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.pool.get('giscedata.polissa.tarifa')
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, 'giscedata_polissa', 'tarifa_20A_test')[1]
            result = model.get_tariff_prices(cursor, uid, tariff_id, 5386, 15000, None, False, False, False)
            self.assertTrue(result)

    def test__get_tariff_prices__tariff_concret_day_OK(self):
        """
        Get an active tariff
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.pool.get('giscedata.polissa.tarifa')
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, 'som_webforms_helpers', 'tarifa_20TD_test')[1]

            tariff = tariff_obj.browse(cursor, uid, tariff_id)

            result = tariff_obj.get_tariff_prices(cursor, uid, tariff_id, 5386, 15000, None, False, '2023-01-15', '2023-01-15')
            prices = [{'bo_social': {'unit': '\xe2\x82\xac/dia', 'value': 0.0},
                'comptador': {'unit': '\xe2\x82\xac/mes', 'value': 0.0},
                'end_date': False,
                'energia': {u'P1': {'unit': '\xe2\x82\xac/kWh', 'value': 0.342},
                u'P2': {'unit': '\xe2\x82\xac/kWh', 'value': 0.281},
                u'P3': {'unit': '\xe2\x82\xac/kWh', 'value': 0.234}},
                'generation_kWh': {u'P1': {'unit': '\xe2\x82\xac/kWh', 'value': 0.17},
                u'P2': {'unit': '\xe2\x82\xac/kWh', 'value': 0.12},
                u'P3': {'unit': '\xe2\x82\xac/kWh', 'value': 0.095}},
                'potencia': {u'P1': {'unit': '\xe2\x82\xac/kW/dia', 'value': 0.074529},
                u'P2': {'unit': '\xe2\x82\xac/kW/dia', 'value': 0.008666}},
                'start_date': '2023-01-01',
                'version_name': u'2.0TD_SOM 2023-01-01'}]

            self.assertEqual(result, prices)

    def test__get_tariff_prices__tariff_concret_range_OK(self):
        """
        Get an active tariff
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.pool.get('giscedata.polissa.tarifa')
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, 'som_webforms_helpers', 'tarifa_20TD_test')[1]

            result = tariff_obj.get_tariff_prices(cursor, uid, tariff_id, 5386, 15000, None, False, '2022-10-15', '2023-01-15')

            prices = [{'bo_social': {'unit': '\xe2\x82\xac/dia', 'value': 0.0},
                'comptador': {'unit': '\xe2\x82\xac/mes', 'value': 0.0},
                'end_date': False,
                'energia': {u'P1': {'unit': '\xe2\x82\xac/kWh', 'value': 0.342},
                u'P2': {'unit': '\xe2\x82\xac/kWh', 'value': 0.281},
                u'P3': {'unit': '\xe2\x82\xac/kWh', 'value': 0.234}},
                'generation_kWh': {u'P1': {'unit': '\xe2\x82\xac/kWh', 'value': 0.17},
                u'P2': {'unit': '\xe2\x82\xac/kWh', 'value': 0.12},
                u'P3': {'unit': '\xe2\x82\xac/kWh', 'value': 0.095}},
                'potencia': {u'P1': {'unit': '\xe2\x82\xac/kW/dia', 'value': 0.074529},
                u'P2': {'unit': '\xe2\x82\xac/kW/dia', 'value': 0.008666}},
                'start_date': '2023-01-01',
                'version_name': u'2.0TD_SOM 2023-01-01'},
                {'bo_social': {'unit': '\xe2\x82\xac/dia', 'value': 0.0},
                'comptador': {'unit': '\xe2\x82\xac/mes', 'value': 0.0},
                'end_date': '2022-12-31',
                'energia': {u'P1': {'unit': '\xe2\x82\xac/kWh', 'value': 0.242},
                u'P2': {'unit': '\xe2\x82\xac/kWh', 'value': 0.181},
                u'P3': {'unit': '\xe2\x82\xac/kWh', 'value': 0.182}},
                'generation_kWh': {u'P1': {'unit': '\xe2\x82\xac/kWh', 'value': 0.0},
                u'P2': {'unit': '\xe2\x82\xac/kWh', 'value': 0.0},
                u'P3': {'unit': '\xe2\x82\xac/kWh', 'value': 0.182}},
                'potencia': {u'P1': {'unit': '\xe2\x82\xac/kW/dia', 'value': 0.047132},
                u'P2': {'unit': '\xe2\x82\xac/kW/dia', 'value': 0.005926}},
                'start_date': '2022-06-01',
                'version_name': u'2.0TD_SOM 2022-06-01'}]

            self.assertEqual(result, prices)


