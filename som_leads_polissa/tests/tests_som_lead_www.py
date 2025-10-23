# -*- encoding: utf-8 -*-
import os
import base64
from datetime import datetime
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
from oopgrade import oopgrade
from tools import config
from osv import osv
import mock


class TestsSomLeadWww(testing.OOTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestsSomLeadWww, cls).setUpClass()
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
                "phone": "972123456",
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

    def test_create_simple_domestic_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        sw_o = self.get_model("giscedata.switching")
        ir_model_o = self.get_model("ir.model.data")
        mailbox_o = self.get_model('poweremail.mailbox')

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        self.assertFalse(result["error"])

        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.name, "40323835M / ES0177000000000000LR")

        # Check that the lead has a valid member number and is the same as the titular
        self.assertTrue(lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref, lead.member_number)

        # Check the member category
        member_category_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_partner_account", "res_partner_category_soci"
        )[1]
        self.assertIn(member_category_id, [c.id for c in lead.polissa_id.soci.category_id])

        # Check that the contract has the member field filled correctly
        self.assertEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        # Check the invoicing mode
        self.assertEqual(lead.polissa_id.facturacio_potencia, "icp")

        # Check that the ATR is created with C1 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C1"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])
        self.assertEqual(atr_case.state, "draft")

        # check default 'contratacion_incondicional_bs'
        c1 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(c1.contratacion_incondicional_bs, "N")

        # Check the pricelist and mode facturacio
        peninsular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        )[1]
        self.assertEqual(lead.polissa_id.llista_preu.id, peninsular_pricelist_id)
        self.assertEqual(lead.polissa_id.mode_facturacio, 'atr')

        # Check that don't have self consumption
        self.assertEqual(lead.polissa_id.autoconsumo, '00')

        # Check the tension (default is 230)
        tensio_230 = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'giscedata_tensions', 'tensio_230')[1]
        self.assertEqual(lead.polissa_id.tensio_normalitzada.id, tensio_230)

        # Check if user_id ("comercial") is created on polissa
        webforms_user_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base_extended_som", "res_users_webforms"
        )[1]
        self.assertEqual(lead.polissa_id.user_id.id, webforms_user_id)

        # Check that the address is correcty created
        self.assertEqual(
            lead.polissa_id.direccio_notificacio.street,
            "Carrer Falsa, 123 BLQ. B ESC. A 5 C"
        )

        # Check the catastral reference
        self.assertEqual(lead.polissa_id.cups.ref_catastral, "9872023VH5797S0001WX")

        # Check that the mail was sent
        template_name = "email_contracte_esborrany_nou_soci"
        template_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', template_name)[1]
        mails = mailbox_o.search(
            self.cursor, self.uid, [
                ("template_id", "=", template_id),
                ("folder", "=", "outbox"),
            ]
        )
        self.assertEqual(len(mails), 1)

        # Check partner lang and member date
        self.assertEqual(lead.partner_id.lang, "es_ES")
        self.assertEqual(lead.partner_id.date, datetime.today().strftime("%Y-%m-%d"))
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_domestic_lead_indexada(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["contract_info"]["is_indexed"] = True
        values["contract_info"]["indexed_contract_terms_accepted"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        peninsular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_peninsula_2024"
        )[1]
        self.assertEqual(lead.polissa_id.llista_preu.id, peninsular_pricelist_id)
        self.assertEqual(lead.polissa_id.mode_facturacio, 'index')
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_juridic_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")

        values = self._basic_values
        values["new_member_info"]["is_juridic"] = True
        values["new_member_info"]["vat"] = "C81837452"
        values["new_member_info"]["name"] = "PEC COOP SCCL"
        values["new_member_info"]["proxy_name"] = "Pepito Palotes"
        values["new_member_info"]["proxy_vat"] = "40323835M"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.is_new_contact, True)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.name, "C81837452 / ES0177000000000000LR")

        # Check that the representative is created and correctly linked
        rep_id = partner_o.search(self.cursor, self.uid, [("vat", "=", "ES40323835M")])[0]
        self.assertEqual(lead.polissa_id.titular.representante_id.id, rep_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_juridic_lead_with_existing_representative(
            self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")
        imd_o = self.get_model('ir.model.data')

        existing_partner_id = imd_o.get_object_reference(
            self.cursor, self.uid, 'base', 'res_partner_agrolait'
        )[1]

        existing_partner_vat = partner_o.read(
            self.cursor, self.uid, existing_partner_id, ['vat']
        )['vat']

        values = self._basic_values
        values["new_member_info"]["is_juridic"] = True
        values["new_member_info"]["vat"] = "C81837452"
        values["new_member_info"]["name"] = "PEC COOP SCCL"
        values["new_member_info"]["proxy_name"] = "Pepito Palotes"
        values["new_member_info"]["proxy_vat"] = existing_partner_vat

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that no new partner is created
        num_repeated_vats = len(
            partner_o.search(self.cursor, self.uid, [("vat", "=", existing_partner_vat)]))
        self.assertEqual(num_repeated_vats, 1)

        # Check that the representative is correctly linked
        self.assertEqual(lead.polissa_id.titular.representante_id.id, existing_partner_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_30TD(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]["tariff"] = "3.0TD"
        values["contract_info"]["powers"] = ["4400", "4900", "5000", "6000", "7000", "15001"]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(len(lead.polissa_id.potencies_periode), 6)
        self.assertEqual(lead.polissa_id.tarifa.name, "3.0TD")
        self.assertEqual(lead.polissa_id.facturacio_potencia, "max")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_donatiu(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["donation"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertIs(lead.polissa_id.donatiu, True)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_owner_change_C2_20TD(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = 'C2'

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the ATR is created with C2 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C2"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])
        self.assertEqual(atr_case.state, "draft")

        # check change type owner
        c2 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(c2.sollicitudadm, "S")
        self.assertEqual(c2.canvi_titular, "T")
        self.assertEqual(c2.control_potencia, "1")

        # check default 'contratacion_incondicional_bs'
        self.assertEqual(c2.contratacion_incondicional_bs, "S")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_owner_change_C2_30TD(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = "C2"
        values["contract_info"]["tariff"] = "3.0TD"
        values["contract_info"]["powers"] = ["4400", "4900", "5000", "6000", "7000", "15001"]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the ATR is created with C2 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C2"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])
        self.assertEqual(atr_case.state, "draft")

        # check change type owner
        c2 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(c2.sollicitudadm, "S")
        self.assertEqual(c2.canvi_titular, "T")
        self.assertEqual(c2.control_potencia, "2")

        # check default contratacion_incondicional_bs
        self.assertEqual(c2.contratacion_incondicional_bs, "S")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_new_cups_A3(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = 'A3'

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        # Check that the ATR is created with A3 process
        atr_case_ids = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "A3"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case_ids), 1)

        atr_case = sw_o.browse(self.cursor, self.uid, atr_case_ids[0])

        a3 = sw_o.get_pas(self.cursor, self.uid, atr_case_ids)
        self.assertEqual(a3.control_potencia, "1")
        self.assertEqual(atr_case.state, "draft")
        self.assertEqual(a3.cnae.name, values["contract_info"]["cnae"])
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_from_canarias(self):
        ir_model_o = self.get_model("ir.model.data")
        cfg_o = self.get_model("res.config")
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values

        laguna_municipi_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_38023"
        )[1]
        tenerife_state_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "l10n_ES_toponyms", "ES38"
        )[1]

        values["contract_info"]["cups_address"]["city_id"] = laguna_municipi_id
        values["contract_info"]["cups_address"]["state_id"] = tenerife_state_id
        values["contract_info"]["cups"] = "ES0031601267738003JC0F"

        canarian_posicio_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "fp_canarias_vivienda"
        )[1]
        cfg_o.set(self.cursor, self.uid, "fp_canarias_vivienda_id", canarian_posicio_id)

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        insular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]

        self.assertEqual(lead.polissa_id.fiscal_position_id.id, canarian_posicio_id)
        self.assertEqual(lead.polissa_id.llista_preu.id, insular_pricelist_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_from_balears(self):
        ir_model_o = self.get_model("ir.model.data")
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values

        capdepera_municipi_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base_extended", "ine_07014"
        )[1]
        balears_state_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "l10n_ES_toponyms", "ES07"
        )[1]

        values["contract_info"]["cups_address"]["city_id"] = capdepera_municipi_id
        values["contract_info"]["cups_address"]["state_id"] = balears_state_id

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        insular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]

        self.assertEqual(lead.polissa_id.llista_preu.id, insular_pricelist_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

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

    def test_add_attachments_to_simple_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")
        ir_attach_o = self.get_model("ir.attachment")

        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'assets', 'blank.pdf'), 'rb') as pdf_file:
            pdf_data = pdf_file.read()

        encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

        values = self._basic_values

        values["attachments"] = [
            {
                "filename": "blank.pdf",
                "datas": encoded_pdf,
                "category": "lead_old_invoice"
            }
        ]

        old_invoice_categ_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "ir_attachment_lead_old_invoice"
        )[1]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        search_params = [
            ("res_model", "=", "giscedata.polissa"),
            ("res_id", "=", lead.polissa_id.id),
            ("category_id", "=", old_invoice_categ_id)
        ]

        ir_attach_ids = ir_attach_o.search(self.cursor, self.uid, search_params)

        self.assertEqual(len(ir_attach_ids), 1)

        # check that the attachment data is not stored in the log
        self.assertNotIn("datas:", lead.polissa_id.observacions)

        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_www_form_data_and_create_entites_log_is_stored(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertIn("name: Pepito", lead.polissa_id.observacions)

        # we check the second line because the first has the stage change
        self.assertIn("ES40323835M", lead.history_line[1].description)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_crm_stages_and_section(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        webform_stage_recieved_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_recieved"
        )[1]

        webform_stage_converted_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_converted"
        )[1]

        webform_stage_error_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_leads_polissa", "webform_stage_error"
        )[1]

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_recieved_id)
        self.assertEqual(lead.crm_id.state, 'open')

        # we need to reload the browse record because the cache
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_converted_id)
        self.assertEqual(lead.crm_id.state, 'done')

        # Test the error stage (cant have 2 leads on the same cups)
        values = self._basic_values
        values["new_member_info"]["vat"] = "53247948G"
        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertTrue(result["error"])
        self.assertEqual(lead.crm_id.state, 'pending')
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_error_id)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_remesable_member(self):
        www_lead_o = self.get_model("som.lead.www")
        account_invoice_o = self.get_model("account.invoice")
        lead_o = self.get_model("giscedata.crm.lead")
        mandate_o = self.get_model("payment.mandate")
        ir_model_o = self.get_model("ir.model.data")
        payment_order_o = self.get_model("payment.order")
        wiz_pay_o = self.get_model('pagar.remesa.wizard')
        ir_sequence_o = self.get_model("ir.sequence")

        # Receveivable payment order should have a different prefix
        rec_payment_order_seq_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "account_payment_extension", "seq_rec_payment_order"
        )[1]
        ir_sequence_o.write(
            self.cursor, self.uid, rec_payment_order_seq_id, {'prefix': 'R%(year)s/'})

        values = self._basic_values
        values["member_payment_type"] = "remesa"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        titular_id = lead.polissa_id.titular.id

        mandate_id = mandate_o.search(
            self.cursor, self.uid, [("reference", "=", "res.partner,{}".format(titular_id))])[0]

        mandate = mandate_o.browse(self.cursor, self.uid, mandate_id)

        self.assertEqual(mandate.payment_type, "one_payment")

        invoice_id = account_invoice_o.search(
            self.cursor, self.uid, [("partner_id", "=", titular_id)])[0]

        invoice = account_invoice_o.browse(self.cursor, self.uid, invoice_id)

        self.assertFalse(invoice.sii_to_send)

        self.assertEqual(invoice.number, "QUOTA-SOCIA-LEAD-{}".format(lead.id))
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.state, "open")

        payment_mode_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "mode_pagament_socis"
        )[1]

        payment_order = invoice.payment_order_id
        self.assertEqual(payment_order.state, 'draft')
        self.assertEqual(payment_order.mode.id, payment_mode_id)
        self.assertEqual(payment_order.total, -100)

        # Pay payment order
        payment_order_o.action_open(self.cursor, self.uid, [payment_order.id])
        with PatchNewCursors():
            context = {'active_ids': [payment_order.id], 'active_id': payment_order.id}
            wiz_pay_id = wiz_pay_o.create(
                self.cursor,
                self.uid,
                {'work_async': False},
                context=context,
            )
            wiz_pay_o.action_pagar_remesa_threaded(self.cursor.dbname, self.uid, [
                                                   wiz_pay_id], context=context)

        po = payment_order_o.browse(self.cursor, self.uid, payment_order.id)
        payment_line_ids = po.line_ids

        # Verify the payment lines after the payment
        for payment_line in payment_line_ids:
            self.assertEqual(payment_line.name, lead.member_number)
            self.assertEqual(payment_line.bank_id.iban, 'ES7712341234161234567890')
            self.assertEqual(payment_line.ml_inv_ref.state, 'paid')
            self.assertEqual(payment_line.order_id.reference, 'R{}/001'.format(datetime.now().year))
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_with_remesa_payment_but_not_new_member(self):
        www_lead_o = self.get_model("som.lead.www")
        account_invoice_o = self.get_model("account.invoice")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        mandate_o = self.get_model("payment.mandate")
        ir_model_o = self.get_model("ir.model.data")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        values["linked_member"] = "sponsored"
        values["contract_owner"] = values.pop("new_member_info")
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }
        values["member_payment_type"] = "remesa"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        titular_id = lead.polissa_id.titular.id

        mandate_id = mandate_o.search(
            self.cursor, self.uid, [("reference", "=", "res.partner,{}".format(titular_id))])

        # No mandate should be created for the titular
        self.assertEqual(len(mandate_id), 0)

        # No invoice should be created for the titular
        invoice_id = account_invoice_o.search(
            self.cursor, self.uid, [("partner_id", "=", titular_id)])
        self.assertEqual(len(invoice_id), 0)

    def test_create_simple_domestic_lead_already_member(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")
        mailbox_o = self.get_model('poweremail.mailbox')
        partner_o = self.get_model("res.partner")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        partner_o.write(self.cursor, self.uid, member.partner_id.id, {'lang': 'ca_ES'})

        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        del values["new_member_info"]
        values["linked_member"] = "already_member"
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.name, "{} / ES0177000000000000LR".format(vat,))

        # Check that the lead has a valid member number and is the same that we entered
        self.assertEqual(member.partner_id.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        # Check that the direccio_notificacio is the already existing partner address
        self.assertEqual(
            lead.polissa_id.direccio_notificacio.street,
            "Major, 32"
        )

        # Check that the mail was sent
        template_name = "email_contracte_esborrany"
        template_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', template_name)[1]
        mails = mailbox_o.search(
            self.cursor, self.uid, [
                ("template_id", "=", template_id),
                ("folder", "=", "outbox"),
            ]
        )
        self.assertEqual(len(mails), 1)

        # Check partner lang
        self.assertEqual(lead.partner_id.lang, "ca_ES")

    def test_create_simple_domestic_lead_sponsored(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")
        mailbox_o = self.get_model('poweremail.mailbox')

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        values["linked_member"] = "sponsored"
        values["contract_owner"] = values.pop("new_member_info")
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.name, "40323835M / ES0177000000000000LR")

        # Check the member number and the different member and titular
        self.assertEqual(member.partner_id.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref[0], "T")
        self.assertNotEqual(lead.polissa_id.titular.ref, lead.member_number)
        self.assertEqual(lead.polissa_id.soci.id, member.partner_id.id)
        self.assertNotEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        # Check that the mail was sent
        template_name = "email_contracte_esborrany"
        template_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'som_polissa_soci', template_name)[1]
        mails = mailbox_o.search(
            self.cursor, self.uid, [
                ("template_id", "=", template_id),
                ("folder", "=", "outbox"),
            ]
        )
        self.assertEqual(len(mails), 1)
        self.mock_subscribe_customer.assert_called()

    def test_bad_linked_member_fails(self):
        www_lead_o = self.get_model("som.lead.www")

        values = self._basic_values
        values["linked_member"] = "Nye he he he he"

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_bad_member_vat_number_data_fails(self):
        www_lead_o = self.get_model("som.lead.www")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        del values["new_member_info"]
        values["linked_member"] = "already_member"
        values["linked_member_info"] = {
            "vat": vat,
            "code": "S000042",  # Just a random different code
        }

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_existing_new_member_vat_fails(self):
        www_lead_o = self.get_model("som.lead.www")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        values["new_member_info"]["vat"] = vat

        with self.assertRaises(osv.except_osv):
            www_lead_o.create_lead(self.cursor, self.uid, values)

    def test_existing_customer_converts_as_member(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")
        ir_model_o = self.get_model("ir.model.data")
        pol_o = self.get_model("giscedata.polissa")
        member_o = self.get_model("somenergia.soci")

        gisce_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_gisce"
        )[1]
        agrolait_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_agrolait"
        )[1]
        gisce_contract = ir_model_o.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_gisce"
        )[1]
        pol_o.write(self.cursor, self.uid, [gisce_contract], {"soci": agrolait_id})
        partner_o.write(self.cursor, self.uid, [gisce_id], {"ref": "P000042"})
        gisce_br = partner_o.browse(self.cursor, self.uid, gisce_id)
        vat = gisce_br.vat.replace("ES", "")

        values = self._basic_values
        values["new_member_info"]["vat"] = vat

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.is_new_contact, False)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        gisce_br = partner_o.browse(self.cursor, self.uid, gisce_id)
        contract_member_id = pol_o.read(
            self.cursor, self.uid, gisce_contract, ['soci'])['soci'][0]
        member_category_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_partner_account", "res_partner_category_soci"
        )[1]

        # Check that the existing customer is now a member
        self.assertEqual(gisce_br.ref[0], "S")
        self.assertIn(member_category_id, [c.id for c in gisce_br.category_id])

        # Check that the existing contract is adopted by the new member
        self.assertEqual(contract_member_id, gisce_id)

        # Check that the member record is created
        member_ids = member_o.search(
            self.cursor, self.uid, [("partner_id", "=", gisce_id)]
        )
        self.assertEqual(len(member_ids), 1)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_lead_with_demographic_data(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["new_member_info"]["gender"] = "non_binary"
        values["new_member_info"]["birthdate"] = "1990-01-01"
        values["new_member_info"]["referral_source"] = "opcions"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(lead.polissa_id.titular.gender, "non_binary")
        self.assertEqual(lead.polissa_id.titular.birthdate, "1990-01-01")
        self.assertEqual(lead.polissa_id.titular.referral_source, "opcions")
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_cnae_random_contract_not_created(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]["cnae"] = "123456789"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.cnae, None)
        self.assertIn("cnae: '123456789'", lead.history_line[1].description)

        with self.assertRaises(osv.except_osv) as e:
            www_lead_o.activate_lead(self.cursor, self.uid,
                                     result["lead_id"], context={"sync": True})
        self.assertIn("CNAE", e.exception.value)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_simple_comercial_info_accepted_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["new_member_info"]["is_juridic"] = True
        values["new_member_info"]["vat"] = "C81837452"
        values["new_member_info"]["name"] = "PEC COOP SCCL"
        values["new_member_info"]["proxy_name"] = "Pepito Palotes"
        values["new_member_info"]["proxy_vat"] = "40323835M"
        values["new_member_info"]["comercial_info_accepted"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.comercial_info_accepted, True)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_create_lead_trifasic_tension(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["contract_info"]["phase"] = "3x230/400"

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"], context={"sync": True})

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        tensio_trifasica = ir_model_o.get_object_reference(
            self.cursor, self.uid, 'giscedata_tensions', 'tensio_3x230_400')[1]
        self.assertEqual(lead.polissa_id.tensio_normalitzada.id, tensio_trifasica)
        self.mock_subscribe_member.assert_called()
        self.mock_unsubscribe_customer.assert_called()

    def test_manual_member_number_error(self):
        www_lead_o = self.get_model("som.lead.www")
        member_o = self.get_model("somenergia.soci")
        ir_model_o = self.get_model("ir.model.data")
        lead_o = self.get_model("giscedata.crm.lead")
        partner_o = self.get_model("res.partner")

        member_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_polissa_soci", "soci_0001"
        )[1]
        member = member_o.browse(self.cursor, self.uid, member_id)
        partner_o.write(self.cursor, self.uid, member.partner_id.id, {'lang': 'ca_ES'})

        vat = member.partner_id.vat.replace("ES", "")

        values = self._basic_values
        values["linked_member"] = "sponsored"
        values["contract_owner"] = values.pop("new_member_info")
        values["linked_member_info"] = {
            "vat": vat,
            "code": member.partner_id.ref.replace("S", ""),
        }

        lead_id = www_lead_o.create_lead(self.cursor, self.uid, values)["lead_id"]
        lead_o.write(
            self.cursor, self.uid, lead_id, {"member_number": "WRONGCODE", "titular_number": ""}
        )

        with self.assertRaises(osv.except_osv):
            lead_o.create_entities(self.cursor, self.uid, lead_id)
