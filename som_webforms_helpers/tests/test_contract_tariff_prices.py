# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime
from destral import testing
import mock

from ..exceptions.som_webforms_exceptions import ContractWithoutModcons, TariffNonExists


class ContractTariffPricesTests(testing.OOTestCase):
    def setUp(self):
        self.model = self.openerp.pool.get("giscedata.polissa.tarifa")
        self.modcontractual = mock.Mock(
            spec=["tarifa", "fiscal_position_id", "potencia"],
            tarifa=mock.Mock(id=43),
            fiscal_position_id=False,
            potencia=4.6,
        )
        # Accessing modcontractuals_ids or draft policy values must fail.
        self.policy = mock.Mock(
            spec=["titular", "modcontractual_activa"],
            titular=mock.Mock(
                vat="ES123",
                address=[mock.Mock(id_municipi=mock.Mock(id=5386))],
            ),
            modcontractual_activa=self.modcontractual,
        )
        self.policy_obj = mock.Mock()
        self.policy_obj.browse.return_value = self.policy
        self.partner_obj = mock.Mock()
        self.partner_obj.is_enterprise_vat.return_value = False
        pool = mock.Mock()
        pool.get.side_effect = lambda model: {
            "giscedata.polissa": self.policy_obj,
            "res.partner": self.partner_obj,
        }[model]
        self.current = {"energia": {"P1": {"value": 0.123, "unit": "EUR/kWh"}}}
        patches = [
            mock.patch.object(self.model, "pool", pool),
            mock.patch.object(
                self.model,
                "get_tariff_prices_by_range",
                return_value={"current": self.current, "history": []},
            ),
            mock.patch("som_webforms_helpers.giscedata_polissa_tarifa.datetime"),
        ]
        started = []
        for patch in patches:
            started.append(patch.start())
            self.addCleanup(patch.stop)
        self.range_prices = started[1]
        started[2].today.return_value = datetime(2026, 10, 19)

    def test_active_tariff_only_without_history(self):
        result = self.model.get_tariff_prices_by_contract_id(None, 1, 17)

        self.policy_obj.browse.assert_called_once_with(None, 1, 17)
        self.range_prices.assert_called_once_with(
            None, 1, 43, 5386, 4600.0, False, False, False,
            "2026-10-19", "2026-10-19", {},
        )
        self.assertEqual(result, {"43": {"current": self.current, "history": []}})

    def test_with_taxes_uses_active_fiscal_position(self):
        self.modcontractual.fiscal_position_id = mock.Mock(id=7)
        self.partner_obj.is_enterprise_vat.return_value = True

        self.model.get_tariff_prices_by_contract_id(None, 1, 17, with_taxes=True)

        self.range_prices.assert_called_once_with(
            None, 1, 43, 5386, 4600.0, 7, True, True,
            "2026-10-19", "2026-10-19", {},
        )

    def test_missing_power_keeps_default(self):
        self.modcontractual.potencia = False

        self.model.get_tariff_prices_by_contract_id(None, 1, 17)

        self.assertEqual(self.range_prices.call_args[0][4], 10000)

    def test_missing_active_modification_keeps_error(self):
        self.policy.modcontractual_activa = False

        with self.assertRaises(ContractWithoutModcons):
            self.model.get_tariff_prices_by_contract_id(None, 1, 17)

        self.range_prices.assert_not_called()
        result = self.model.get_tariff_prices_by_contract_id_www(None, 1, 17)
        self.assertEqual(result["error_code"], "ContractWithoutModcons")

    def test_missing_prices_keeps_www_error(self):
        self.range_prices.side_effect = TariffNonExists()

        result = self.model.get_tariff_prices_by_contract_id_www(None, 1, 17)

        self.assertEqual(result["error_code"], "TariffNonExists")
        self.range_prices.assert_called_once()

    def test_empty_current_keeps_response_shape(self):
        self.range_prices.return_value = {"current": {}, "history": []}

        result = self.model.get_tariff_prices_by_contract_id_www(None, 1, 17)

        self.assertEqual(result, {"43": {"current": {}, "history": []}})

    def test_context_is_not_modified_by_price_calculation(self):
        context = {"lang": "ca_ES", "date": "2020-01-01"}

        def prices(*args):
            args[-1]["date"] = "2026-01-01"
            args[-1]["pricelist_base_price"] = 0.0
            return {"current": self.current, "history": []}

        self.range_prices.side_effect = prices
        self.model.get_tariff_prices_by_contract_id(None, 1, 17, context=context)

        self.assertEqual(context, {"lang": "ca_ES", "date": "2020-01-01"})
        self.assertEqual(self.range_prices.call_args[0][8:10], ("2026-10-19", "2026-10-19"))
        self.assertEqual(self.range_prices.call_args[0][-1]["lang"], "ca_ES")
