# -*- encoding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from oopgrade import oopgrade
from tools import config
import mock


class BaseSomLeadWwwTest(testing.OOTestCase):
    @classmethod
    def setUpClass(cls):
        super(BaseSomLeadWwwTest, cls).setUpClass()
        with Transaction().start(config['db_name']) as txn:
            oopgrade.load_data(
                txn.cursor, "giscedata_facturacio_comer", 'distribuidores_data.xml', mode='update'
            )
            txn.cursor.commit()

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        lang_o = self.get_model("res.lang")
        ir_model_o = self.get_model("ir.model.data")
        stage_validation_template_o = self.get_model("crm.stage.validation.template")

        lang_o.create(self.cursor, self.uid, {"name": "Català", "code": "ca_ES"})
        lang_o.create(self.cursor, self.uid, {"name": "Español", "code": "es_ES"})

        # Remove a demo data that changes the stage validation behaviour
        no_stage_validation_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "giscedata_crm_leads", "demo_crm_lead_no_stage_validation"
        )[1]
        stage_validation_template_o.unlink(self.cursor, self.uid, no_stage_validation_id)

        self._basic_values = {
            "linked_member": "new_member",
            "new_member_info": {
                "vat": "40323835M",
                "name": "Pepito",
                "surname": "Palotes",
                "is_juridic": False,
                "address": {
                    "state_id": 20,
                    "city_id": 5386,
                    "postal_code": "08178",
                    "street": "Carrer Falsa",
                    "number": "123",
                    "floor": "5",
                    "stair": "A",
                    "door": "C",
                    "block": "B",
                },
                "email": "pepito@foo.bar",
                "phone": "+34 972123456",
                "lang": "es_ES",
                "privacy_conditions": True,
            },
            "contract_info": {
                "cups": "ES0177000000000000LR",
                "is_indexed": False,
                "tariff": "2.0TD",
                "powers": ["4400", "8000"],
                "phase": "230",
                "cnae": "9820",
                "process": "C1",
                "cups_cadastral_reference": "9872023VH5797S0001WX",
                "cups_address": {
                    "state_id": 20,
                    "city_id": 5386,
                    "postal_code": "08178",
                    "street": "Carrer Falsa",
                    "number": "123",
                    "floor": "5",
                    "stair": "A",
                    "door": "C",
                    "block": "B",
                },
            },
            "iban": "ES7712341234161234567890",
            "member_payment_type": "tpv",
            "donation": False,
            "general_contract_terms_accepted": True,
            "particular_contract_terms_accepted": True,
            "sepa_conditions": True,
        }

        # 1. Crear els patchers per a Mailchimp
        self.patch_subscribe_member = mock.patch(
            "som_polissa_soci.models.res_partner_address.ResPartnerAddress.subscribe_partner_in_members_lists"  # noqa: E501
        )
        self.patch_unsubscribe_customer = mock.patch(
            "som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists"  # noqa: E501
        )
        self.patch_subscribe_customer = mock.patch(
            "som_polissa_soci.models.res_partner_address.ResPartnerAddress.subscribe_partner_in_customers_no_members_lists"  # noqa: E501
        )
        self.mock_subscribe_member = self.patch_subscribe_member.start()
        self.mock_unsubscribe_customer = self.patch_unsubscribe_customer.start()
        self.mock_subscribe_customer = self.patch_subscribe_customer.start()

    def tearDown(self):
        self.patch_subscribe_member.stop()
        self.patch_unsubscribe_customer.stop()
        self.patch_subscribe_customer.stop()
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)
