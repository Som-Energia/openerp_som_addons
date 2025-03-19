# -*- encoding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestsSomLeadWww(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def test_create_simple_lead(self):
        self.get_model("ir.model.data")
        www_lead_o = self.get_model("som.lead.www")

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
            "cups": "ES0122449351050857YA",
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

        www_lead_o.create_lead(self.cursor, self.uid, values)
