# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import datetime
from ..exceptions.som_webforms_exceptions import TariffNonExists
from giscedata_facturacio_iva_10.giscedata_facturacio_iva_10 import GiscedataMonthlyPriceOmie
import mock


class tarifes_tests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get("ir.model.data")
        self.tariff_model = self.pool.get("giscedata.polissa.tarifa")
        self.res_config = self.pool.get("res.config")

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
            model = self.tariff_model
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "tarifa_20A_test"
            )[1]
            result = model.get_tariff_prices_by_range(
                cursor, uid, tariff_id, 5386, 15000, None, False, False, "2021-12-01", "2021-12-01"
            )
            self.assertTrue(result)

    def test__get_tariff_prices__invalid_date(self):
        """
        Checks that given a tariff and a date there are not prices in that date
        :return: error.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            model = self.tariff_model
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "tarifa_20A_test"
            )[1]

            with self.assertRaises(TariffNonExists) as ctx:
                model.get_tariff_prices_by_range(
                    cursor,
                    uid,
                    tariff_id,
                    5386,
                    15000,
                    None,
                    False,
                    False,
                    "1999-12-01",
                    "1999-12-01",
                )

            self.assertEqual(ctx.exception.to_dict()["error"], "Tariff pricelist not found")

    def test__get_tariff_prices_by_contract_id__no_titular(self):
        """
        Checks that given a contract without titular an error is launched
        :return: error.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            model = self.tariff_model
            pol_obj = self.pool.get("giscedata.polissa")

            polissa_id = self.imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]
            pol_obj.write(cursor, uid, [polissa_id], {"titular": False})

            result = model.get_tariff_prices_by_contract_id_www(cursor, uid, polissa_id, False)

            self.assertTrue(result["error"])

    def test__get_tariff_prices__valid_date_range_date_tariff_into_range(self):

        date_start = "2022-12-01"
        date_end = "2023-01-31"

        date_from = "2021-01-01"
        date_to = "2023-02-01"

        self.assertTrue(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__valid_date_range_date_from_into_tariff(self):

        date_start = "2022-12-01"
        date_end = "2023-01-31"

        date_from = "2022-12-15"
        date_to = "2023-02-01"

        self.assertTrue(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__valid_date_range_date_to_into_tariff(self):

        date_start = "2022-12-01"
        date_end = "2023-01-31"

        date_from = "2021-01-01"
        date_to = "2023-01-15"

        self.assertTrue(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__valid_date_range_date_range_into_tariff(self):

        date_start = "2022-12-01"
        date_end = "2023-01-31"

        date_from = "2021-12-15"
        date_to = "2023-01-15"

        self.assertTrue(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__valid_date_range_date_range_equal_tariff_range(self):

        date_start = "2022-12-01"
        date_end = "2023-01-31"

        date_from = "2021-12-01"
        date_to = "2023-01-31"

        self.assertTrue(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__valid_date_range_date_range_before_tariff_range(self):

        date_start = "2022-12-01"
        date_end = "2023-01-31"

        date_from = "2020-12-01"
        date_to = "2022-01-31"

        self.assertFalse(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__valid_date_range_date_range_after_tariff_range(self):

        date_start = "2022-12-01"
        date_end = "2023-01-31"

        date_from = "2023-12-01"
        date_to = "2024-01-31"

        self.assertFalse(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__valid_date_range_with_active_tariff(self):

        date_start = "2022-12-01"
        date_end = False

        date_from = "2022-12-15"
        date_to = "2024-01-31"

        self.assertTrue(
            (not date_end or date_from <= date_end) and (not date_start or date_to >= date_start)
        )

    def test__get_tariff_prices__without_dates(self):
        """
        Get an active tariff
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            model = self.tariff_model
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "tarifa_20A_test"
            )[1]
            result = model.get_tariff_prices_by_range(
                cursor, uid, tariff_id, 5386, 15000, None, False, False, False, False
            )
            self.assertTrue(result)

    def test__get_tariff_prices__tariff_concret_day_OK(self):
        """
        Get an active tariff
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "som_webforms_helpers", "tarifa_20TD_test"
            )[1]

            tariff_obj.browse(cursor, uid, tariff_id)

            today = datetime.today().strftime("%Y-%m-%d")

            result = tariff_obj.get_tariff_prices_by_range(
                cursor, uid, tariff_id, 5386, 15000, None, False, False, today, today
            )
            prices = {
                "current": {
                    "bo_social": {"unit": "\xe2\x82\xac/dia", "value": 0.0},
                    "comptador": {"unit": "\xe2\x82\xac/mes", "value": 0.0},
                    "end_date": False,
                    "energia": {
                        u"P1": {"unit": "\xe2\x82\xac/kWh", "value": 0.342},
                        u"P2": {"unit": "\xe2\x82\xac/kWh", "value": 0.281},
                        u"P3": {"unit": "\xe2\x82\xac/kWh", "value": 0.234},
                    },
                    "fiscal_position": False,
                    "generation_kWh": {
                        u"P1": {"unit": "\xe2\x82\xac/kWh", "value": 0.17},
                        u"P2": {"unit": "\xe2\x82\xac/kWh", "value": 0.12},
                        u"P3": {"unit": "\xe2\x82\xac/kWh", "value": 0.095},
                    },
                    "potencia": {
                        u"P1": {"unit": "\xe2\x82\xac/kW/dia", "value": 0.074325},
                        u"P2": {"unit": "\xe2\x82\xac/kW/dia", "value": 0.008642},
                    },
                    "reactiva": {},
                    "start_date": "2023-01-01",
                    "version_name": u"2.0TD_SOM 2023-01-01",
                },
                "history": [],
            }

            self.assertEqual(result, prices)

    def test__get_tariff_prices__tariff_concret_range_OK(self):
        """
        Get an active tariff
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "som_webforms_helpers", "tarifa_20TD_test"
            )[1]

            result = tariff_obj.get_tariff_prices_by_range(
                cursor, uid, tariff_id, 5386, 15000, None, False, False, "2022-10-15", "2023-01-15"
            )
            prices = {
                "current": {
                    "bo_social": {"unit": "\xe2\x82\xac/dia", "value": 0.0},
                    "comptador": {"unit": "\xe2\x82\xac/mes", "value": 0.0},
                    "end_date": False,
                    "energia": {
                        u"P1": {"unit": "\xe2\x82\xac/kWh", "value": 0.342},
                        u"P2": {"unit": "\xe2\x82\xac/kWh", "value": 0.281},
                        u"P3": {"unit": "\xe2\x82\xac/kWh", "value": 0.234},
                    },
                    "fiscal_position": False,
                    "generation_kWh": {
                        u"P1": {"unit": "\xe2\x82\xac/kWh", "value": 0.17},
                        u"P2": {"unit": "\xe2\x82\xac/kWh", "value": 0.12},
                        u"P3": {"unit": "\xe2\x82\xac/kWh", "value": 0.095},
                    },
                    "potencia": {
                        u"P1": {"unit": "\xe2\x82\xac/kW/dia", "value": 0.074325},
                        u"P2": {"unit": "\xe2\x82\xac/kW/dia", "value": 0.008642},
                    },
                    "reactiva": {},
                    "start_date": "2023-01-01",
                    "version_name": u"2.0TD_SOM 2023-01-01",
                },
                "history": [
                    {
                        "bo_social": {"unit": "\xe2\x82\xac/dia", "value": 0.0},
                        "comptador": {"unit": "\xe2\x82\xac/mes", "value": 0.0},
                        "end_date": "2022-12-31",
                        "energia": {
                            u"P1": {"unit": "\xe2\x82\xac/kWh", "value": 0.242},
                            u"P2": {"unit": "\xe2\x82\xac/kWh", "value": 0.181},
                            u"P3": {"unit": "\xe2\x82\xac/kWh", "value": 0.182},
                        },
                        "fiscal_position": False,
                        "generation_kWh": {
                            u"P1": {"unit": "\xe2\x82\xac/kWh", "value": 0.0},
                            u"P2": {"unit": "\xe2\x82\xac/kWh", "value": 0.0},
                            u"P3": {"unit": "\xe2\x82\xac/kWh", "value": 0.182},
                        },
                        "potencia": {
                            u"P1": {"unit": "\xe2\x82\xac/kW/dia", "value": 0.047003},
                            u"P2": {"unit": "\xe2\x82\xac/kW/dia", "value": 0.00591},
                        },
                        "start_date": "2022-06-01",
                        "version_name": u"2.0TD_SOM 2022-06-01",
                    }
                ],
            }

            self.assertEqual(result, prices)

    def test__get_dades_modcontractuals__reduce_equal_data(self):
        tariff_obj = self.tariff_model

        modcon_data = [
            (43, False, 3.4, "2021-06-01", "2023-11-21"),
            (1, False, 3.4, "2019-09-02", "2021-05-31"),
            (1, False, 6.6, "2014-12-17", "2019-09-01"),
            (1, False, 6.6, "2014-09-17", "2014-12-16"),
            (1, False, 6.6, "2011-11-22", "2014-09-16"),
        ]

        result = tariff_obj._get_dades_modcontractuals(modcon_data)

        pricelist_data = [
            (43, False, 3.4, "2021-06-01", "2023-11-21"),
            (1, False, 3.4, "2019-09-02", "2021-05-31"),
            (1, False, 6.6, "2011-11-22", "2019-09-01"),
        ]

        pricelist_data.reverse()

        self.assertEqual(result, pricelist_data)

    def test__get_dades_modcontractuals__reduce_last_element(self):
        tariff_obj = self.tariff_model

        modcon_data = [
            (43, False, 3.4, "2021-06-01", "2023-11-21"),
            (43, False, 3.4, "2019-09-02", "2021-05-31"),
            (1, False, 6.6, "2014-12-17", "2019-09-01"),
            (1, False, 6.6, "2014-09-17", "2014-12-16"),
            (1, False, 6.6, "2011-11-22", "2014-09-16"),
        ]

        result = tariff_obj._get_dades_modcontractuals(modcon_data)

        pricelist_data = [
            (43, False, 3.4, "2019-09-02", "2023-11-21"),
            (1, False, 6.6, "2011-11-22", "2019-09-01"),
        ]

        pricelist_data.reverse()

        self.assertEqual(result, pricelist_data)

    def test__get_dades_modcontractuals__unordered_data(self):
        tariff_obj = self.tariff_model

        modcon_data = [
            (1, False, 6.6, "2014-12-17", "2019-09-01"),
            (43, False, 3.4, "2021-06-01", "2023-11-21"),
            (1, False, 6.6, "2014-09-17", "2014-12-16"),
            (43, False, 3.4, "2019-09-02", "2021-05-31"),
            (1, False, 6.6, "2011-11-22", "2014-09-16"),
        ]

        result = tariff_obj._get_dades_modcontractuals(modcon_data)

        pricelist_data = [
            (43, False, 3.4, "2019-09-02", "2023-11-21"),
            (1, False, 6.6, "2011-11-22", "2019-09-01"),
        ]

        pricelist_data.reverse()

        self.assertEqual(result, pricelist_data)

    def test__get_max_power_by_tariff__max_power(self):
        tariff_obj = self.tariff_model

        result = tariff_obj._get_max_power_by_tariff("2.0TD")

        self.assertEqual(result, 15000)

    def test__get_max_power_by_tariff__none(self):
        tariff_obj = self.tariff_model

        result = tariff_obj._get_max_power_by_tariff("")

        self.assertEqual(result, None)

    def test__get_fiscal_position_igic__home(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            afp_obj = self.pool.get("account.fiscal.position")

            result = tariff_obj._get_fiscal_position_igic(
                cursor, uid, "2022-10-01", "2023-01-15", True
            )

            expected_result = [("2021-06-01", "2999-12-31", afp_obj.browse(cursor, uid, 33))]
            self.assertEqual(result, expected_result)

    def test__combine_pricelist_fiscal_position__pricelist_data(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            tariff_obj = self.tariff_model
            pplv_obj = self.pool.get("product.pricelist.version")
            imd_obj = self.pool.get("ir.model.data")

            pricelist_2022_id = imd_obj.get_object_reference(
                cursor,
                uid,
                "som_webforms_helpers",
                "version_pricelist_tarifas_electricidad_20TD_SOM_20220601",
            )[1]
            pricelist_2023_id = imd_obj.get_object_reference(
                cursor,
                uid,
                "som_webforms_helpers",
                "version_pricelist_tarifas_electricidad_20TD_SOM_20230101",
            )[1]

            pricelists_ids = [pricelist_2022_id, pricelist_2023_id]
            pricelists = [pricelist for pricelist in pplv_obj.browse(cursor, uid, pricelists_ids)]

            fiscal_positions = [("2000-01-01", "2999-12-31", 1), ("2022-10-01", "2022-12-31", 2)]

            result = tariff_obj._combine_pricelist_fiscal_position(pricelists, fiscal_positions)

            expected_result = [
                (
                    pplv_obj.browse(cursor, uid, pricelist_2022_id),
                    {"fp": 1, "fp_date_start": "2000-01-01", "fp_date_end": "2999-12-31"},
                ),
                (
                    pplv_obj.browse(cursor, uid, pricelist_2022_id),
                    {"fp": 2, "fp_date_start": "2022-10-01", "fp_date_end": "2022-12-31"},
                ),
                (
                    pplv_obj.browse(cursor, uid, pricelist_2023_id),
                    {"fp": 1, "fp_date_start": "2000-01-01", "fp_date_end": "2999-12-31"},
                ),
            ]
            self.assertEqual(result, expected_result)

    def test__get_tariff_prices__current_tariff_OK(self):
        """
        Get an active tariff
        :return: a dictionary with the prices of the given tariff.
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            tariff_id = self.imd_obj.get_object_reference(
                cursor, uid, "som_webforms_helpers", "tarifa_20TD_test"
            )[1]

            result = tariff_obj.get_tariff_prices(
                cursor, uid, tariff_id, 5386, 15000, None, False, "2022-10-15"
            )

            prices = {
                "bo_social": {"uom": "\xe2\x82\xac/dia", "value": 0.0},
                "comptador": {"uom": "\xe2\x82\xac/mes", "value": 0.0},
                "end_date": "2022-12-31",
                "gkwh": {
                    u"P1": {"uom": "\xe2\x82\xac/kWh", "value": 0.0},
                    u"P2": {"uom": "\xe2\x82\xac/kWh", "value": 0.0},
                    u"P3": {"uom": "\xe2\x82\xac/kWh", "value": 0.182},
                },
                "start_date": "2022-06-01",
                u"te": {
                    u"P1": {"uom": "\xe2\x82\xac/kWh", "value": 0.242},
                    u"P2": {"uom": "\xe2\x82\xac/kWh", "value": 0.181},
                    u"P3": {"uom": "\xe2\x82\xac/kWh", "value": 0.182},
                },
                u"tp": {
                    u"P1": {"uom": "\xe2\x82\xac/kW/dia", "value": 0.047003},
                    u"P2": {"uom": "\xe2\x82\xac/kW/dia", "value": 0.00591},
                },
                "version_name": u"2.0TD_SOM 2022-06-01",
            }

            self.assertEqual(result, prices)

    @mock.patch.object(GiscedataMonthlyPriceOmie, "has_to_charge_10_percent_requeriments_oficials")
    def test___get_fiscal_position_reduced__apply(self, mock_omie_price):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            self.res_config.set(cursor, uid, 'charge_iva_10_percent_when_available', 1)
            mock_omie_price.return_value = True

            result = tariff_obj._get_fiscal_position_reduced(
                cursor, uid, 10000, "2022-06-15", "2022-06-30"
            )

            self.assertEqual(result[0][0], u'2021-06-01')
            self.assertEqual(result[0][1], u'2024-12-31')
            self.assertEqual(result[0][2].id, 31)

    def test___get_fiscal_position_reduced__max_power_gt_10000__NOTapply(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            self.res_config.set(cursor, uid, 'charge_iva_10_percent_when_available', 1)

            result = tariff_obj._get_fiscal_position_reduced(
                cursor, uid, 15000, "2022-06-15", "2022-06-30"
            )

            self.assertEqual(result, [])

    def test___get_fiscal_position_reduced__reduction_not_active__NOTapply(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            self.res_config.set(cursor, uid, 'charge_iva_10_percent_when_available', 0)

            result = tariff_obj._get_fiscal_position_reduced(
                cursor, uid, 10000, "2022-06-15", "2022-06-30"
            )

            self.assertEqual(result, [])

    @mock.patch.object(GiscedataMonthlyPriceOmie, "has_to_charge_10_percent_requeriments_oficials")
    def test___get_fiscal_position_reduced__not_omie_price__NOTapply(self, mock_omie_price):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            tariff_obj = self.tariff_model
            self.res_config.set(cursor, uid, 'charge_iva_10_percent_when_available', 1)
            mock_omie_price.return_value = False

            result = tariff_obj._get_fiscal_position_reduced(
                cursor, uid, 10000, "2022-06-15", "2022-06-30"
            )

            self.assertEqual(result, [])
