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

        # tipuspersona (fisica o juridica)
        # nom
        # cognom
        # dni
        # representant_nom (si es juridica)
        # representant_dni (si es juridica)
        # tel
        # tel2 (opcional)
        # email
        # cp
        # provincia
        # adreca
        # municipi
        # idioma (es_ES o ca_ES -> https://api.somenergia.coop/data/idiomes)
        # payment_method (tpv, rebut, remesa)
        # payment_iban (si es remesa)

        values = {
            "member_number": "38434",
            "member_vat": "40323835M",
            "cups": "ES0122449351050857YA",
            "is_indexed": False,
            "tariff": "2.0TD",
            "power_p1": "4400",
            "power_p2": "8000",
            "cups_address": "Pedro López, 13",
            "cups_postal_code": "17003",
            "cups_city_id": 5386,
            "cups_state_id": 20,
            "cnae": "9820",
            "supply_point_accepted": True,
            "owner_is_member": True,
            "owner_is_payer": True,
            "payment_iban": "ES77 1234 1234 1612 3456 7890",
            "sepa_conditions": True,
            "donation": True,
            "process": "C1",
            "general_contract_terms_accepted": True,
            "particular_contract_terms_accepted": True,
            "self_consumption": {
                "cau": "ES0353501028615353EE0FA000",
                "collective_installation": True,
                "installation_power": "3500",
                "installation_type": "01",
                "technology": "b11",
                "aux_services": False
            }
        }

        www_lead_o.create_lead(values)
