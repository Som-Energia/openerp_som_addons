# -*- encoding: utf-8 -*-
import os
import base64
from destral import testing
from destral.transaction import Transaction
from oopgrade import oopgrade
from tools import config


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
                "cnae": "9820",
                "process": "C1",  # TODO: It comes from webforms?
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
            "supply_point_accepted": True,  # TODO: It comes from webforms?
            "general_contract_terms_accepted": True,
            "particular_contract_terms_accepted": True,
            "sepa_conditions": True,
        }

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def test_create_simple_domestic_lead(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        sw_o = self.get_model("giscedata.switching")
        ir_model_o = self.get_model("ir.model.data")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        self.assertFalse(result["error"])

        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.name, "40323835M / ES0177000000000000LR")

        # Check that the lead has a valid member number and is the same as the titular
        self.assertTrue(lead.member_number)
        self.assertEqual(lead.polissa_id.titular.ref, lead.member_number)

        # Check that the contract has the member field filled correctly
        self.assertEqual(lead.polissa_id.soci, lead.polissa_id.titular)

        # Check the invoicing mode
        self.assertEqual(lead.polissa_id.facturacio_potencia, "icp")

        # Check that the ATR is created with C1 process
        atr_case = sw_o.search(
            self.cursor, self.uid, [
                ("proces_id.name", "=", "C1"),
                ("cups_polissa_id", "=", lead.polissa_id.id),
                ("cups_input", "=", lead.polissa_id.cups.name),
            ]
        )
        self.assertEqual(len(atr_case), 1)

        # Check the pricelist and mode facturacio
        peninsular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        )[1]
        self.assertEqual(lead.polissa_id.llista_preu.id, peninsular_pricelist_id)
        self.assertEqual(lead.polissa_id.mode_facturacio, 'atr')

        # Check that don't have self consumption
        self.assertEqual(lead.polissa_id.autoconsumo, '00')

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

    def test_create_simple_domestic_lead_indexada(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")
        ir_model_o = self.get_model("ir.model.data")

        values = self._basic_values
        values["contract_info"]["is_indexed"] = True
        values["contract_info"]["indexed_contract_terms_accepted"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        peninsular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_peninsula_2024"
        )[1]
        self.assertEqual(lead.polissa_id.llista_preu.id, peninsular_pricelist_id)
        self.assertEqual(lead.polissa_id.mode_facturacio, 'index')

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        # Check that the name is correctly set
        self.assertEqual(lead.name, "C81837452 / ES0177000000000000LR")

        # Check that the representative is created and correctly linked
        rep_id = partner_o.search(self.cursor, self.uid, [("vat", "=", "ES40323835M")])[0]
        self.assertEqual(lead.polissa_id.titular.representante_id.id, rep_id)

    def test_create_simple_juridic_lead_with_existing_representative(self):
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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

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
        values["contract_info"]["tariff"] = "3.0TD"
        values["contract_info"]["powers"] = ["4400", "4900", "5000", "6000", "7000", "15001"]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertEqual(len(lead.polissa_id.potencies_periode), 6)
        self.assertEqual(lead.polissa_id.tarifa.name, "3.0TD")
        self.assertEqual(lead.polissa_id.facturacio_potencia, "max")

    def test_create_lead_with_donatiu(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["donation"] = True

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertIs(lead.polissa_id.donatiu, True)

    def test_create_lead_with_owner_change_C2_20TD(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = 'C2'

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

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

    def test_create_lead_with_owner_change_C2_30TD(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = "C2"
        values["contract_info"]["tariff"] = "3.0TD"
        values["contract_info"]["powers"] = ["4400", "4900", "5000", "6000", "7000", "15001"]

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

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

    def test_create_lead_with_new_cups_A3(self):
        www_lead_o = self.get_model("som.lead.www")
        sw_o = self.get_model("giscedata.switching")
        lead_o = self.get_model("giscedata.crm.lead")

        values = self._basic_values
        values["contract_info"]['process'] = 'A3'

        result = www_lead_o.create_lead(self.cursor, self.uid, values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        insular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]

        self.assertEqual(lead.polissa_id.fiscal_position_id.id, canarian_posicio_id)
        self.assertEqual(lead.polissa_id.llista_preu.id, insular_pricelist_id)

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        insular_pricelist_id = ir_model_o.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]

        self.assertEqual(lead.polissa_id.llista_preu.id, insular_pricelist_id)

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

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

    def test_create_colective_multiconsumption_self_consumption_lead(self):
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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        search_params = [
            ("res_model", "=", "giscedata.polissa"),
            ("res_id", "=", lead.polissa_id.id),
            ("category_id", "=", old_invoice_categ_id)
        ]

        ir_attach_ids = ir_attach_o.search(self.cursor, self.uid, search_params)

        self.assertEqual(len(ir_attach_ids), 1)

    def test_www_form_data_and_create_entites_log_is_stored(self):
        www_lead_o = self.get_model("som.lead.www")
        lead_o = self.get_model("giscedata.crm.lead")

        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])

        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])

        self.assertIn("name: Pepito", lead.polissa_id.observacions)

        # we check the second line because the first has the stage change
        self.assertIn("ES40323835M", lead.history_line[1].description)

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
        www_lead_o.activate_lead(self.cursor, self.uid, result["lead_id"])
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_converted_id)
        self.assertEqual(lead.crm_id.state, 'done')

        # Test the error stage (cant have 2 leads on the same cups)
        result = www_lead_o.create_lead(self.cursor, self.uid, self._basic_values)
        lead = lead_o.browse(self.cursor, self.uid, result["lead_id"])
        self.assertTrue(result["error"])
        self.assertEqual(lead.crm_id.state, 'pending')
        self.assertEqual(lead.crm_id.stage_id.id, webform_stage_error_id)
