# -*- encoding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestsSomLeadWww(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        lang_o = self.get_model("res.lang")

        lang_o.create(self.cursor, self.uid, {"name": "Català", "code": "ca_ES"})
        lang_o.create(self.cursor, self.uid, {"name": "Español", "code": "es_ES"})

        self._basic_values = {
            "owner_is_member": True,
            "owner_is_payer": True,
            "contract_member": {
                "vat": "40323835M",
                "name": "Pepito",
                "surname": "Palotes",
                "is_juridic": False,
                "address": "C/ Falsa, 123",
                "city_id": 5386,
                "state_id": 20,
                "postal_code": "08178",
                "email": "pepito@foo.bar",
                "phone": "972123456",
                "lang": "es_ES",
                "privacy_conditions": True,
            },
            "cups": "ES0177000000000000LR",
            "is_indexed": False,
            "tariff": "2.0TD",
            "power_p1": "4400",
            "power_p2": "8000",
            "cups_address": "C/ Falsa, 123",
            "cups_postal_code": "08178",
            "cups_city_id": 5386,
            "cups_state_id": 20,
            "cnae": "9820",
            "supply_point_accepted": True,
            "payment_iban": "ES77 1234 1234 1612 3456 7890",
            "sepa_conditions": True,
            "donation": False,
            "process": "C1",
            "general_contract_terms_accepted": True,
            "particular_contract_terms_accepted": True,
        }

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def test_create_simple_domestic_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        sw_o = self.get_model("giscedata.switching")

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead_o.force_validation(self.cursor, self.uid, [lead_id])
        lead_o.create_entities(self.cursor, self.uid, lead_id)

        lead = lead_o.browse(self.cursor, self.uid, lead_id)
        # Check that the name is correctly set
        self.assertEqual(lead.name, "40323835M / ES0177000000000000LR")

        # Check that the lead has a valid member number and is the same as the titular
        self.assertTrue(lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref, lead.member_number)

        # Check that the contract has the member field filled correctly
        self.assertEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        # Check that the ATR is created with C1 process
        atr_case = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C1"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case), 1)

    def test_create_simple_juridic_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")

        values = self._basic_values
        values["contract_member"]["is_juridic"] = True
        values["contract_member"]["vat"] = "C81837452"
        values["contract_member"]["name"] = "PEC COOP SCCL"
        values["contract_member"]["proxy_name"] = "Pepito Palotes"
        values["contract_member"]["proxy_vat"] = "40323835M"

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead_o.force_validation(self.cursor, self.uid, [lead_id])
        lead_o.create_entities(self.cursor, self.uid, lead_id)

        lead = lead_o.browse(self.cursor, self.uid, lead_id)
        # Check that the name is correctly set
        self.assertEqual(lead.name, "C81837452 / ES0177000000000000LR")

        # Check that the representative is created and correctly linked
        rep_id = partner_o.search(self.cursor, self.uid, [("vat", "=", "ES40323835M")])[0]
        self.assertEqual(lead.polissa_id.titular.representante_id.id, rep_id)

    def test_create_simple_juridic_lead_with_existing_representative(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")
        imd_o = self.openerp.pool.get('ir.model.data')

        existing_partner_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'som_leads_polissa', 'res_partner_distri'
        )[1]

        existing_partner_vat = partner_o.read(
            self.cursor, self.uid, existing_partner_id, ['vat']
        )['vat']

        values = self._basic_values
        values["contract_member"]["is_juridic"] = True
        values["contract_member"]["vat"] = "C81837452"
        values["contract_member"]["name"] = "PEC COOP SCCL"
        values["contract_member"]["proxy_name"] = "Pepito Palotes"
        values["contract_member"]["proxy_vat"] = existing_partner_vat

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead_o.force_validation(self.cursor, self.uid, [lead_id])
        lead_o.create_entities(self.cursor, self.uid, lead_id)

        lead = lead_o.browse(self.cursor, self.uid, lead_id)

        # Check that no new partner is created
        num_repeated_vats = len(
            partner_o.search(self.cursor, self.uid, [("vat", "=", existing_partner_vat)]))
        self.assertEqual(num_repeated_vats, 1)

        # Check that the representative is correctly linked
        self.assertEqual(lead.polissa_id.titular.representante_id.id, existing_partner_id)

    def test_create_lead_30TD(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["tariff"] = "3.0TD"
        values["power_p1"] = "4400"
        values["power_p2"] = "4900"
        values["power_p3"] = "5000"
        values["power_p4"] = "6000"
        values["power_p5"] = "7000"
        values["power_p6"] = "15001"

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead_o.force_validation(self.cursor, self.uid, [lead_id])
        lead_o.create_entities(self.cursor, self.uid, lead_id)

        lead = lead_o.browse(self.cursor, self.uid, lead_id)

        self.assertEqual(len(lead.polissa_id.potencies_periode), 6)
        self.assertEqual(lead.polissa_id.tarifa.name, "3.0TD")

    def test_create_lead_with_donatiu(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["donation"] = True

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead_o.force_validation(self.cursor, self.uid, [lead_id])
        lead_o.create_entities(self.cursor, self.uid, lead_id)

        lead = lead_o.browse(self.cursor, self.uid, lead_id)
        self.assertIs(lead.polissa_id.donatiu, True)
