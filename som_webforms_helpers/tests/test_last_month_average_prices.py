# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction
import mock


class LastMonthAveragePricesTests(testing.OOTestCase):
    def setUp(self):
        self.model = self.openerp.pool.get("giscedata.polissa.tarifa")
        self.average_obj = self.openerp.pool.get("som.last.month.average.price")

    def _create_average(self, cursor, uid, tariff="2.0TD", price_type="index",
                        date="2026-04-01", price=0.123456):
        values = dict(("p%d_price" % period, price) for period in range(1, 7))
        values.update(tariff=tariff, type=price_type, date=date)
        return self.average_obj.create(cursor, uid, values)

    def _clear_averages(self, cursor, uid):
        ids = self.average_obj.search(cursor, uid, [])
        self.average_obj.unlink(cursor, uid, ids)

    def test_response_for_each_tariff_and_type(self):
        with Transaction().start(self.database) as txn:
            cursor, uid = txn.cursor, txn.user
            self._clear_averages(cursor, uid)
            for tariff in ("2.0TD", "3.0TD"):
                for price_type in ("index", "ssaa"):
                    self._create_average(cursor, uid, tariff, price_type)
                    result = self.model.get_last_month_average_prices_www(
                        cursor, uid, tariff, price_type
                    )
                    self.assertEqual(result, {
                        "tariff": tariff,
                        "type": price_type,
                        "date": "2026-04-01",
                        "prices": dict(
                            ("P%d" % period, {"value": 0.123456, "uom": u"€/kWh"})
                            for period in range(1, 7)
                        ),
                    })

    def test_each_period_returns_its_own_price(self):
        with Transaction().start(self.database) as txn:
            cursor, uid = txn.cursor, txn.user
            self._clear_averages(cursor, uid)
            self.average_obj.create(cursor, uid, {
                "tariff": "3.0TD",
                "type": "index",
                "date": "2026-04-01",
                "p1_price": 0.123456,
                "p2_price": 0.234567,
                "p3_price": 0.345678,
                "p4_price": 0.456789,
                "p5_price": 0.567891,
                "p6_price": 0.678912,
            })

            result = self.model.get_last_month_average_prices_www(cursor, uid, "3.0TD", "index")

            self.assertEqual(result["prices"]["P1"], {"value": 0.123456, "uom": u"€/kWh"})
            self.assertEqual(result["prices"]["P2"], {"value": 0.234567, "uom": u"€/kWh"})
            self.assertEqual(result["prices"]["P3"], {"value": 0.345678, "uom": u"€/kWh"})
            self.assertEqual(result["prices"]["P4"], {"value": 0.456789, "uom": u"€/kWh"})
            self.assertEqual(result["prices"]["P5"], {"value": 0.567891, "uom": u"€/kWh"})
            self.assertEqual(result["prices"]["P6"], {"value": 0.678912, "uom": u"€/kWh"})

    def test_latest_date_then_id_and_no_month_filter(self):
        with Transaction().start(self.database) as txn:
            cursor, uid = txn.cursor, txn.user
            self._clear_averages(cursor, uid)
            self._create_average(cursor, uid, date="2026-06-01", price=0.2)
            self._create_average(cursor, uid, date="2026-05-01", price=0.1)
            self._create_average(cursor, uid, date="2026-06-01", price=0.3)
            self._create_average(cursor, uid, tariff="3.0TD", date="2026-07-01", price=0.4)
            self._create_average(cursor, uid, price_type="ssaa", date="2026-07-01", price=0.5)
            context = {"date": "2020-01-01", "lang": "ca_ES"}

            result = self.model.get_last_month_average_prices_www(
                cursor, uid, "2.0TD", "index", context=context
            )

            self.assertEqual(result["date"], "2026-06-01")
            self.assertEqual(result["prices"], dict(
                ("P%d" % p, {"value": 0.3, "uom": u"€/kWh"}) for p in range(1, 7)
            ))
            self.assertEqual(context, {"date": "2020-01-01", "lang": "ca_ES"})

    def test_zero_prices_are_valid(self):
        with Transaction().start(self.database) as txn:
            cursor, uid = txn.cursor, txn.user
            self._clear_averages(cursor, uid)
            self._create_average(cursor, uid, price=0.0)

            result = self.model.get_last_month_average_prices_www(cursor, uid, "2.0TD", "index")

            self.assertEqual(result["prices"], dict(
                ("P%d" % p, {"value": 0.0, "uom": u"€/kWh"}) for p in range(1, 7)
            ))
            self.assertNotIn("error", result)

    def test_missing_configuration(self):
        with Transaction().start(self.database) as txn:
            cursor, uid = txn.cursor, txn.user
            self._clear_averages(cursor, uid)
            # Other tariffs or types must not act as a fallback.
            self._create_average(cursor, uid, tariff="3.0TD")
            self._create_average(cursor, uid, price_type="ssaa")

            result = self.model.get_last_month_average_prices_www(cursor, uid, "2.0TD", "index")

            self.assertEqual(result["error_code"], "MissingSimulationConfig")
            self.assertEqual(result["error"], "Simulation configuration not found")
            self.assertNotIn("prices", result)

    def test_invalid_tariff_does_not_query_prices(self):
        with mock.patch.object(self.average_obj, "get_current_price") as get_price:
            for tariff in ("6.1TD", "", False, None, 123, [], {}):
                result = self.model.get_last_month_average_prices_www(None, 1, tariff, "index")
                self.assertEqual(result["error_code"], "InvalidAveragePriceTariff")
                self.assertEqual(result["error"], "Average price tariff must be '2.0TD' or '3.0TD'")
                self.assertNotIn("prices", result)
            get_price.assert_not_called()

    def test_invalid_type_does_not_query_prices(self):
        with mock.patch.object(self.average_obj, "get_current_price") as get_price:
            for price_type in ("periods", "", False, None, 123, [], {}):
                result = self.model.get_last_month_average_prices_www(None, 1, "2.0TD", price_type)
                self.assertEqual(result["error_code"], "InvalidAveragePriceType")
                self.assertEqual(result["error"], "Average price type must be 'index' or 'ssaa'")
                self.assertNotIn("prices", result)
            get_price.assert_not_called()

    def test_delegates_with_same_user_and_context(self):
        context = {"lang": "ca_ES"}
        with mock.patch.object(
            self.average_obj, "get_current_price", return_value=False
        ) as get_price:
            self.model.get_last_month_average_prices_www(None, 7, "3.0TD", "ssaa", context=context)

        get_price.assert_called_once_with(None, 7, "3.0TD", "ssaa", context=context)

    def test_unexpected_error_uses_webforms_format(self):
        with mock.patch.object(
            self.average_obj, "get_current_price", side_effect=RuntimeError("test")
        ):
            result = self.model.get_last_month_average_prices_www(None, 1, "2.0TD", "index")

        self.assertEqual(result["error_code"], "Unexpected")
        self.assertEqual(result["error"], "test")
        self.assertIn("trace", result)
        self.assertNotIn("prices", result)
