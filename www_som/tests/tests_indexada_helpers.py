# -*- coding: utf-8 -*-
from som_indexada.tests.test_wizard_change_to_indexada import TestChangeToIndexada
from datetime import datetime, timedelta
import json


class TestIndexadaHelpers(TestChangeToIndexada):
    def test_change_to_indexada_www__with_indexada_exception(self):
        polissa_obj = self.pool.get("giscedata.polissa")
        polissa_id = self.get_contract_id(self.txn, xml_id="polissa_tarifa_018")
        self.switch(self.txn, "comer")
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(self.txn, context=None)
        polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])
        context = {"active_id": polissa_id, "change_type": "from_period_to_index"}
        self.create_case_and_step(self.cursor, self.uid, polissa_id, "M1", "01")

        helper = self.pool.get("som.indexada.webforms.helpers")

        result = helper.change_to_indexada_www(self.cursor, self.uid, polissa_id, context)

        self.assertEqual(result["error"], u"Pòlissa 0018 with simultaneous ATR")

    def test_change_to_indexada_www__to_indexed(self):
        polissa_id = self.open_polissa("polissa_tarifa_018")
        polissa_obj = self.pool.get("giscedata.polissa")
        modcon_obj = self.pool.get("giscedata.polissa.modcontractual")
        IrModel = self.pool.get("ir.model.data")

        context = {"active_id": polissa_id, "change_type": "from_period_to_index"}

        helper = self.pool.get("som.indexada.webforms.helpers")

        helper.change_to_indexada_www(self.cursor, self.uid, polissa_id, context)

        modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][0]
        prev_modcontactual_id = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["modcontractuals_ids"]
        )["modcontractuals_ids"][1]

        new_pricelist_id = IrModel._get_obj(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_peninsula_2024"
        ).id

        modcon_act = modcon_obj.read(
            self.cursor,
            self.uid,
            modcontactual_id,
            [
                "data_inici",
                "data_final",
                "mode_facturacio",
                "mode_facturacio_generacio",
                "llista_preu",
                "active",
                "state",
                "modcontractual_ant",
            ],
        )
        modcon_act.pop("id")
        modcon_act["llista_preu"] = modcon_act["llista_preu"][0]
        modcon_act["modcontractual_ant"] = modcon_act["modcontractual_ant"][0]

        self.assertEquals(
            modcon_act,
            {
                "data_inici": datetime.strftime(datetime.today() + timedelta(days=1), "%Y-%m-%d"),
                "data_final": datetime.strftime(datetime.today() + timedelta(days=365), "%Y-%m-%d"),
                "mode_facturacio": "index",
                "mode_facturacio_generacio": "index",
                "llista_preu": new_pricelist_id,
                "active": True,
                "state": "pendent",
                "modcontractual_ant": prev_modcontactual_id,
            },
        )

    def test__get_energy_prices__invalid_geozone(self):
        helper = self.pool.get("som.indexada.webforms.helpers")

        result = helper.get_indexed_prices(
            self.cursor, self.uid, 'invalid_geo_zone', '2.0TD', '2021-12-01', '2021-12-01'
        )

        self.assertEqual(result["error"], "Wrong geo zone invalid_geo_zone")

    def test__get_energy_prices__invalid_tariff(self):
        helper = self.pool.get("som.indexada.webforms.helpers")

        result = helper.get_indexed_prices(
            self.cursor, self.uid, 'PENINSULA', 'invalid_tariff', '2021-12-01', '2021-12-01'
        )

        self.assertEqual(result["error"], "Tariff invalid_tariff not found")

    def test__get_energy_prices__invalid_dates(self):
        helper = self.pool.get("som.indexada.webforms.helpers")

        result = helper.get_indexed_prices(
            self.cursor, self.uid, 'PENINSULA', '2.0TD', '2022-12-01', '2021-12-01'
        )

        self.assertEqual(result["error"], "Invalid range dates [2022-12-01 - 2021-12-01]")

    def test__get_energy_prices__ok(self):
        helper = self.pool.get("som.indexada.webforms.helpers")

        result = helper.get_indexed_prices(
            self.cursor, self.uid, 'PENINSULA', '2.0TDTest', '2023-05-01', '2023-05-01'
        )
        expected = {
            "last_date": "2023-05-02 00:00:00",
            "first_date": "2023-05-01 01:00:00",
            "curves": {
                "geo_zone": "PENINSULA",
                "maturity": ["C3", "C3", "C3", "C3", "C3", None, None, None, None,
                             None, None, None, None, None, None, None, None, None,
                             None, None, None, None, None, None],
                "tariff": "2.0TDTest",
                "price_euros_kwh": [0.2, 0.3, 0.4, 0.5, 0.6, None, None, None, None,
                                    None, None, None, None, None, None, None, None,
                                    None, None, None, None, None, None, None]
            }
        }
        self.assertDictEqual(json.loads(result), expected)

    def test__get_energy_prices_repeated_prices__ok(self):
        helper = self.pool.get("som.indexada.webforms.helpers")

        prices_obj = self.pool.get('giscedata.next.days.energy.price')
        tariff_obj = self.pool.get('giscedata.polissa.tarifa')

        tariff_id = tariff_obj.search(self.cursor, self.uid, [('name', '=', '2.0TDTest')])

        values = {"name": "hour7",
                  "tarifa_id": tariff_id[0],
                  "geom_zone": "PENINSULA",
                  "prm_diari": 1.7,
                  "initial_price": 0.7,
                  "maturity": "C3.3",
                  "hour_timestamp": "2023-05-01 01:00:00",
                  "season": 'S',
                  "id": 7,
                  "file_date": "2023-05-03 00:00:00",
                  "initial_file_date": "2023-05-03 00:00:00",
                  }

        prices_obj.create(self.cursor, self.uid, values)

        result = helper.get_indexed_prices(
            self.cursor, self.uid, 'PENINSULA', '2.0TDTest', '2023-05-01', '2023-05-01'
        )

        expected = {
            "last_date": "2023-05-02 00:00:00",
            "first_date": "2023-05-01 01:00:00",
            "curves": {
                "geo_zone": "PENINSULA",
                "maturity": ["C3.3", "C3", "C3", "C3", "C3", None, None, None, None,
                             None, None, None, None, None, None, None, None, None,
                             None, None, None, None, None, None],
                "tariff": "2.0TDTest",
                "price_euros_kwh": [0.7, 0.3, 0.4, 0.5, 0.6, None, None, None, None,
                                    None, None, None, None, None, None, None, None,
                                    None, None, None, None, None, None, None]
            }
        }
        self.assertDictEqual(json.loads(result), expected)

    def test__get_compensation_prices__ok(self):
        helper = self.pool.get("som.indexada.webforms.helpers")

        result = helper.get_compensation_prices(
            self.cursor, self.uid, 'PENINSULA', '2023-05-01', '2023-05-01'
        )

        expected = {
            "last_date": "2023-05-02 00:00:00",
            "first_date": "2023-05-01 01:00:00",
            "curves": {
                "geo_zone": "PENINSULA",
                "maturity": ["C3", "C3", "C3", "C3", "C3", None, None, None, None, None,
                             None, None, None, None, None, None, None, None, None, None,
                             None, None, None, None],
                "compensation_euros_kwh": [0.0012, 0.0013, 0.0014, 0.0015, 0.0016,
                                           None, None, None, None, None, None, None,
                                           None, None, None, None, None, None, None,
                                           None, None, None, None, None]
            }
        }
        self.assertDictEqual(json.loads(result), expected)

    def test__initial_final_times__24h(self):
        first_date = '2024-02-29'
        last_date = '2024-02-29'
        helper = self.pool.get("som.indexada.webforms.helpers")

        initial_time, final_time = helper.initial_final_times(first_date, last_date)

        self.assertEqual(initial_time, '2024-02-29 01:00:00')
        self.assertEqual(final_time, '2024-03-01 00:00:00')
