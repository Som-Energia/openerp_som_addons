# -*- encoding: utf-8 -*-
from __future__ import absolute_import


from .base_som_lead_www import BaseSomLeadWwwTest


class TestLeadWwwSelfConsumption(BaseSomLeadWwwTest):
    def test_create_self_consumption_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        self_consumption_o = self.get_model("giscedata.autoconsum")
        generator_o = self.get_model("giscedata.autoconsum.generador")

        values = self._basic_values
        values["self_consumption"] = {
            "cau": "ES0353501028615353EE0FA000",
            "collective_installation": False,
            "installation_power": "3500",
            "installation_type": "01",
            "technology": "b11",
            "aux_services": False,
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Buscar el CAU
        self_consumption_ids = self_consumption_o.search(
            self.cursor, self.uid, [("cau", '=', values["self_consumption"]["cau"])]
        )
        self.assertEqual(len(self_consumption_ids), 1)

        # Look if there is our CUPS in CAU
        self_consumption_cups = self_consumption_o.browse(
            self.cursor, self.uid, self_consumption_ids[0]
        )
        self.assertEqual(
            self_consumption_cups.cups_id[0].name[:-2], values["contract_info"]["cups"])

        # A Generator for our CAU exists
        generator_ids = generator_o.search(
            self.cursor, self.uid, [("autoconsum_id", "=", self_consumption_ids[0])]
        )
        self.assertEqual(len(generator_ids), 1)

        # Check Contract fields
        self.assertNotEqual(lead.polissa_id.tipus_subseccio, "00")
        self.assertEqual(lead.polissa_id.autoconsumo, '41')
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_collective_self_consumption_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        self_consumption_o = self.get_model("giscedata.autoconsum")
        generator_o = self.get_model("giscedata.autoconsum.generador")

        values = self._basic_values
        values["self_consumption"] = {
            "cau": "ES0353501028615353EE0FA000",
            "collective_installation": True,
            "installation_power": "3500",
            "installation_type": "01",
            "technology": "b11",
            "aux_services": False,
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Buscar el CAU
        self_consumption_ids = self_consumption_o.search(
            self.cursor, self.uid, [("cau", '=', values["self_consumption"]["cau"])]
        )
        self.assertEqual(len(self_consumption_ids), 1)

        # Look if there is our CUPS in CAU
        self_consumption_cups = self_consumption_o.browse(
            self.cursor, self.uid, self_consumption_ids[0]
        )
        self.assertEqual(
            self_consumption_cups.cups_id[0].name[:-2], values["contract_info"]["cups"])

        # A Generator for our CAU exists
        generator_ids = generator_o.search(
            self.cursor, self.uid, [("autoconsum_id", "=", self_consumption_ids[0])]
        )
        self.assertEqual(len(generator_ids), 1)

        # Check Contract fields
        self.assertNotEqual(lead.polissa_id.tipus_subseccio, "00")
        self.assertEqual(lead.polissa_id.autoconsumo, '42')
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_colective_multiconsumption_self_consumption_lead(
            self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        self_consumption_o = self.get_model("giscedata.autoconsum")
        generator_o = self.get_model("giscedata.autoconsum.generador")

        values = self._basic_values
        values["self_consumption"] = {
            "cau": "ES0353501028615353EE0FA000",
            "collective_installation": True,
            "installation_power": "3500",
            "installation_type": "02",
            "technology": "b11",
            "aux_services": False,
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Buscar el CAU
        self_consumption_ids = self_consumption_o.search(
            self.cursor, self.uid, [("cau", '=', values["self_consumption"]["cau"])]
        )
        self.assertEqual(len(self_consumption_ids), 1)

        # Look if there is our CUPS in CAU
        self_consumption_cups = self_consumption_o.browse(
            self.cursor, self.uid, self_consumption_ids[0]
        )
        self.assertEqual(
            self_consumption_cups.cups_id[0].name[:-2], values["contract_info"]["cups"])

        # A Generator for our CAU exists
        generator_ids = generator_o.search(
            self.cursor, self.uid, [("autoconsum_id", "=", self_consumption_ids[0])]
        )
        self.assertEqual(len(generator_ids), 1)

        # Check Contract fields
        self.assertNotEqual(lead.polissa_id.tipus_subseccio, "00")
        self.assertEqual(lead.polissa_id.autoconsumo, '42')
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_collective_net_self_consumption_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        self_consumption_o = self.get_model("giscedata.autoconsum")
        generator_o = self.get_model("giscedata.autoconsum.generador")

        values = self._basic_values
        values["self_consumption"] = {
            "cau": "ES0353501028615353EE0FA000",
            "collective_installation": True,
            "installation_power": "3500",
            "installation_type": "03",
            "technology": "b11",
            "aux_services": False,
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Buscar el CAU
        self_consumption_ids = self_consumption_o.search(
            self.cursor, self.uid, [("cau", '=', values["self_consumption"]["cau"])]
        )
        self.assertEqual(len(self_consumption_ids), 1)

        # Look if there is our CUPS in CAU
        self_consumption_cups = self_consumption_o.browse(
            self.cursor, self.uid, self_consumption_ids[0]
        )
        self.assertEqual(
            self_consumption_cups.cups_id[0].name[:-2], values["contract_info"]["cups"])

        # A Generator for our CAU exists
        generator_ids = generator_o.search(
            self.cursor, self.uid, [("autoconsum_id", "=", self_consumption_ids[0])]
        )
        self.assertEqual(len(generator_ids), 1)

        # Check Contract fields
        self.assertNotEqual(lead.polissa_id.tipus_subseccio, "00")
        self.assertEqual(lead.polissa_id.autoconsumo, '43')
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_individual_net_self_consumption_lead_fails(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["self_consumption"] = {
            "cau": "ES0353501028615353EE0FA000",
            "collective_installation": False,
            "installation_power": "3500",
            "installation_type": "03",
            "technology": "b11",
            "aux_services": False,
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        self.assertTrue(result["error"])
