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

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def test_create_simple_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = {
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

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead_o.force_validation(self.cursor, self.uid, [lead_id])
        lead_o.create_entities(self.cursor, self.uid, lead_id)

        lead = lead_o.browse(self.cursor, self.uid, lead_id)
        # Comprovació de s'ha creat la sòcia - en el titular
        self.assertTrue(lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref, lead.member_number)

        # Comprovació de s'ha creat la sòcia - a la polissa
        self.assertEqual(lead.polissa_id.soci, lead.polissa_id.titular)

    # def test_create_godfathered_lead(self):
    #     www_lead_o = self.get_model("som.lead.www")
    #     lead_o = self.get_model("giscedata.crm.lead")

    #     values = {
    #         "owner_is_member": True,
    #         "owner_is_payer": True,
    #         "contract_member": {
    #             "vat": "40323835M",
    #             "name": "Pepito",
    #             "surname": "Palotes",
    #             "is_juridic": False,
    #             "address": "C/ Falsa, 123",
    #             "city_id": 5386,
    #             "state_id": 20,
    #             "postal_code": "08178",
    #             "email": "pepito@foo.bar",
    #             "phone": "972123456",
    #             "lang": "es_ES",
    #             "privacy_conditions": True,
    #         },
    #         "cups": "ES0177000000000000LR",
    #         "is_indexed": False,
    #         "tariff": "2.0TD",
    #         "power_p1": "4400",
    #         "power_p2": "8000",
    #         "cups_address": "C/ Falsa, 123",
    #         "cups_postal_code": "08178",
    #         "cups_city_id": 5386,
    #         "cups_state_id": 20,
    #         "cnae": "9820",
    #         "supply_point_accepted": True,
    #         "payment_iban": "ES77 1234 1234 1612 3456 7890",
    #         "sepa_conditions": True,
    #         "donation": False,
    #         "process": "C1",
    #         "general_contract_terms_accepted": True,
    #         "particular_contract_terms_accepted": True,
    #     }

    #     lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)
    #     # Comprovació de s'ha creat la sòcia - en el lead
    #     member_lead_vals = lead_o.read(self.cursor, self.uid, lead_id, ["member_vat"])

    #     self.assertEqual(member_lead_vals["member_vat"], values["contract_member"]["vat"])
