# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import date, timedelta, datetime
from addons import get_module_resource
import mock

from .. import giscedata_atc, giscedata_polissa, som_autoreclama_state_history


def today_str():
    return date.today().strftime("%Y-%m-%d")


def today_minus_str(d):
    return (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")


class SomAutoreclamaBaseTests(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def search_in(self, model, params):
        model_obj = self.get_model(model)
        found_ids = model_obj.search(self.cursor, self.uid, params)
        return found_ids[0] if found_ids else None

    def browse_referenced(self, reference):
        model, id = reference.split(",")
        model_obj = self.get_model(model)
        return model_obj.browse(self.cursor, self.uid, int(id))

    def get_object_reference(self, module, semantic_id):
        ir_obj = self.get_model("ir.model.data")
        expected_id = ir_obj.get_object_reference(
            self.cursor, self.uid, module, semantic_id
        )
        return expected_id

    def create_tags(self):
        tag_obj = self.get_model("giscedata.atc.tag")
        tag_obj.create(self.cursor, self.uid, {
            'name': "[GET] Expedient FRAU",
            'description': "Bla bla bla",
        })
        tag_obj.create(self.cursor, self.uid, {
            'name': "[GET] Expedient ANOMALIA",
            'description': "Bla bla bla",
        })


class SomAutoreclamaStatesTest(SomAutoreclamaBaseTests):
    def test_first_state_correct_atc_dummy(self):
        _, correct_state_id = self.get_object_reference(
            "som_autoreclama", "correct_state_workflow_atc"
        )
        sas_obj = self.get_model("som.autoreclama.state")
        first = sas_obj.browse(self.cursor, self.uid, correct_state_id)
        self.assertEqual(first.name, "Correcte")

    def test_first_state_correct_polissa_dummy(self):
        _, correct_state_id = self.get_object_reference(
            "som_autoreclama", "correct_state_workflow_polissa"
        )
        sas_obj = self.get_model("som.autoreclama.state")
        first = sas_obj.browse(self.cursor, self.uid, correct_state_id)
        self.assertEqual(first.name, "Correcte")

    @mock.patch.object(som_autoreclama_state_history.SomAutoreclamaStateHistoryAtc, "create")
    @mock.patch.object(giscedata_atc.GiscedataAtc, "create")
    def _test_create_atc__state_correct_in_history(self, mock_create_atc, mock_create_history):
        sash_obj = self.get_model("som.autoreclama.state.history.atc")
        mock_create_atc.return_value = 1

        def create_history_mock(cursor, uid, id, vals):
            return {}

        mock_create_history.side_effect = create_history_mock

        atc_obj = self.get_model("giscedata.atc")
        atc_obj.create(self.cursor, self.uid, {})

        vals = {"atc_id": 1, "state_id": 1, "change_date": today_str()}
        sash_obj.create.assert_called_once_with(self.cursor, self.uid, vals)

    @mock.patch.object(som_autoreclama_state_history.SomAutoreclamaStateHistoryPolissa, "create")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "create")
    def _test_create_polissa__state_correct_in_history(self, mock_create_polissa, mock_create_history):  # noqa: E501
        sash_obj = self.get_model("som.autoreclama.state.history.atc")
        mock_create_polissa.return_value = 1

        def create_history_mock(cursor, uid, id, vals):
            return {}

        mock_create_history.side_effect = create_history_mock

        pol_obj = self.get_model("giscedata.polissa")
        pol_id = pol_obj.create(self.cursor, self.uid, {})

        vals = {"polissa_id": pol_id, "state_id": 1, "change_date": today_str()}
        sash_obj.create.assert_called_once_with(self.cursor, self.uid, vals)

    def test_create_atc__first_state_correct_in_history_indirectly(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0001"
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "client")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "029")])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": False,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.autoreclama_state.name, "Correcte")
        self.assertEqual(atc.autoreclama_state_date, today_str())
        self.assertEqual(len(atc.autoreclama_history_ids), 1)

    def test_create_atc__first_state_correct_in_history_indirectly_a(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0001"
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "client")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "029")])

        state_0_id = self.search_in("som.autoreclama.state", [("name", "ilike", "correc")])
        state_0_dt = "2022-01-02"

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": False,
        }
        ctxt = {
            "autoreclama_history_initial_state_id": state_0_id,
            "autoreclama_history_initial_date": state_0_dt,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, ctxt
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.autoreclama_state.id, state_0_id)
        self.assertEqual(atc.autoreclama_state_date, state_0_dt)
        self.assertEqual(len(atc.autoreclama_history_ids), 1)

    def test_historize__second_state_correct_in_history_indirectly(self):
        atc_obj = self.get_model("giscedata.atc")
        history_obj = self.get_model("som.autoreclama.state.history.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0001"
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "client")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "029")])

        state_0_id = self.search_in("som.autoreclama.state", [("name", "ilike", "correc")])
        state_0_dt = "2022-01-02"
        state_1_id = self.search_in("som.autoreclama.state", [("name", "ilike", "desact")])
        state_1_dt = "2022-02-15"
        state_1_st = 2

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": False,
        }
        ctxt = {
            "autoreclama_history_initial_state_id": state_0_id,
            "autoreclama_history_initial_date": state_0_dt,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, ctxt
        )
        state_1_st = new_atc_id
        history_obj.historize(self.cursor, self.uid, new_atc_id, state_1_id, state_1_dt, state_1_st)

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.autoreclama_state.id, state_1_id)
        self.assertEqual(atc.autoreclama_state_date, state_1_dt)
        self.assertEqual(len(atc.autoreclama_history_ids), 2)

        self.assertEqual(atc.autoreclama_history_ids[1].state_id.id, state_0_id)
        self.assertEqual(atc.autoreclama_history_ids[1].change_date, state_0_dt)
        self.assertEqual(atc.autoreclama_history_ids[1].end_date, state_1_dt)
        self.assertEqual(atc.autoreclama_history_ids[1].atc_id.id, new_atc_id)
        self.assertEqual(atc.autoreclama_history_ids[1].generated_atc_id.id, False)

    def test_historize__third_state_correct_in_history_indirectly(self):
        atc_obj = self.get_model("giscedata.atc")
        history_obj = self.get_model("som.autoreclama.state.history.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0001"
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "client")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "029")])
        state_0_id = self.search_in("som.autoreclama.state", [("name", "ilike", "correc")])
        state_0_dt = "2022-01-02"
        state_1_id = self.search_in("som.autoreclama.state", [("name", "ilike", "reclam")])
        state_1_dt = "2022-02-15"
        state_1_st = 3
        state_2_id = self.search_in("som.autoreclama.state", [("name", "ilike", "desact")])
        state_2_dt = "2022-04-16"
        state_2_st = 4

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": False,
        }
        ctxt = {
            "autoreclama_history_initial_state_id": state_0_id,
            "autoreclama_history_initial_date": state_0_dt,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, ctxt
        )

        state_1_st = state_2_st = new_atc_id
        history_obj.historize(self.cursor, self.uid, new_atc_id, state_1_id, state_1_dt, state_1_st)
        history_obj.historize(self.cursor, self.uid, new_atc_id, state_2_id, state_2_dt, state_2_st)

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.autoreclama_state.id, state_2_id)
        self.assertEqual(atc.autoreclama_state_date, state_2_dt)
        self.assertEqual(len(atc.autoreclama_history_ids), 3)

        self.assertEqual(atc.autoreclama_history_ids[1].state_id.id, state_1_id)
        self.assertEqual(atc.autoreclama_history_ids[1].change_date, state_1_dt)
        self.assertEqual(atc.autoreclama_history_ids[1].end_date, state_2_dt)
        self.assertEqual(atc.autoreclama_history_ids[1].atc_id.id, new_atc_id)
        self.assertEqual(atc.autoreclama_history_ids[1].generated_atc_id.id, state_1_st)

        self.assertEqual(atc.autoreclama_history_ids[2].state_id.id, state_0_id)
        self.assertEqual(atc.autoreclama_history_ids[2].change_date, state_0_dt)
        self.assertEqual(atc.autoreclama_history_ids[2].end_date, state_1_dt)
        self.assertEqual(atc.autoreclama_history_ids[2].atc_id.id, new_atc_id)
        self.assertEqual(atc.autoreclama_history_ids[2].generated_atc_id.id, False)


class SomAutoreclamaCreationWizardTest(SomAutoreclamaBaseTests):
    def test_create_general_atc_r1_case_via_wizard__atr_wihtout_r1_type_a(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0001"
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "client")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "029")])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": False,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name, new_case_data["descripcio"])
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, new_case_data["tanca_al_finalitzar_r1"])
        self.assertEqual(atc.ref, False)

    def test_create_general_atc_r1_case_via_wizard__atr_wihtout_r1_type_b(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0002"
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "directo")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "switching")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "011")])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per que si",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": False,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name, new_case_data["descripcio"])
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, new_case_data["tanca_al_finalitzar_r1"])
        self.assertEqual(atc.ref, False)

    def test_create_general_atc_r1_case_via_wizard__atr_wihtout_r1_type_c(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0003"
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "fono")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "auto")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "030")])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per si de cas",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": False,
            "crear_cas_r1": False,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name, new_case_data["descripcio"])
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, new_case_data["tanca_al_finalitzar_r1"])
        self.assertEqual(atc.ref, False)

    def test_create_general_atc_r1_case_via_wizard__atr_with_r1_type_a(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0002"
        )

        par1_id = self.search_in("res.partner", [("name", "ilike", "Tiny sprl")])
        par2_id = self.search_in("res.partner", [("name", "ilike", "ASUStek")])
        par_obj = self.get_model("res.partner")
        par_obj.write(self.cursor, self.uid, par1_id, {"ref": "58264"})
        par_obj.write(self.cursor, self.uid, par2_id, {"ref": "58265"})

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "client")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "029")])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": True,
            "crear_cas_r1": True,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name, new_case_data["descripcio"])
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, new_case_data["tanca_al_finalitzar_r1"])

        atr = self.browse_referenced(atc.ref)

        self.assertEqual(atr.proces_id.name, u"R1")
        self.assertEqual(atr.step_id.name, u"01")
        self.assertEqual(atr.section_id.name, u"Switching")
        self.assertEqual(atr.cups_polissa_id.id, polissa_id)
        self.assertEqual(atr.state, u"open")
        self.assertEqual(atr.ref, u"giscedata.atc, {}".format(atc.id))

    def test_create_ATC_R1_029_from_atc_via_wizard__from_atr(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0002"
        )

        par1_id = self.search_in("res.partner", [("name", "ilike", "Tiny sprl")])
        par2_id = self.search_in("res.partner", [("name", "ilike", "ASUStek")])
        par_obj = self.get_model("res.partner")
        par_obj.write(self.cursor, self.uid, par1_id, {"ref": "58264"})
        par_obj.write(self.cursor, self.uid, par2_id, {"ref": "58265"})

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        section_id = self.search_in("crm.case.section", [("name", "ilike", "client")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "029")])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": True,
            "crear_cas_r1": True,
        }
        old_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )

        new_atc_id = atc_obj.create_ATC_R1_029_from_atc_via_wizard(
            self.cursor, self.uid, old_atc_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)
        atc_old = atc_obj.browse(self.cursor, self.uid, old_atc_id)

        self.assertEqual(atc.name, new_case_data["descripcio"])
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, new_case_data["tanca_al_finalitzar_r1"])
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        codi_solicitud_old = self.browse_referenced(atc_old.ref).codi_sollicitud
        cas_atr = self.browse_referenced(atc.ref)
        pas_atr_id = cas_atr.step_ids[0].pas_id
        pas_atr = self.browse_referenced(pas_atr_id)
        codi_solicitud_ref = pas_atr.reclamacio_ids[0].codi_sollicitud_reclamacio
        self.assertEqual(codi_solicitud_old, codi_solicitud_ref)

    def test_create_ATC_R1_006_from_polissa_via_wizard__from_atc(self):
        atc_obj = self.get_model("giscedata.atc")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0002"
        )

        par1_id = self.search_in("res.partner", [("name", "ilike", "Tiny sprl")])
        par2_id = self.search_in("res.partner", [("name", "ilike", "ASUStek")])
        par_obj = self.get_model("res.partner")
        par_obj.write(self.cursor, self.uid, par1_id, {"ref": "58264"})
        par_obj.write(self.cursor, self.uid, par2_id, {"ref": "58265"})

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "006")])
        _, section_id = self.get_object_reference(
            "som_switching", "atc_section_factura"
        )

        new_atc_id = atc_obj.create_ATC_R1_006_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name, u"AUTOCAC 006")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, True)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

    def test_create_ATC_R1_010_from_f1_via_wizard__f1_non_C(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "N",
        })

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
                self.cursor, self.uid, f1_id, {}
            )

        msg = u"Error en la creació del CAC amb R1 010, F1 no es tipus C id_f1 {}".format(f1_id)
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_010_from_f1_via_wizard__f1_C_no_lines(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
                self.cursor, self.uid, f1_id, {}
            )

        msg = u"Error en la creació del CAC amb R1 010, F1 sense linies id_f1 {}".format(f1_id)
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_010_from_f1_via_wizard__f1_C_bad_line(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })

        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
                self.cursor, self.uid, f1_id, {}
            )

        msg = u"Error en la creació del CAC amb R1 010, F1 no es tipus anomalia o frau id_f1 {}".format(f1_id)  # noqa: E501
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_010_from_f1_via_wizard__f1_C_line_anomalia(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })

        new_atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
            self.cursor, self.uid, f1_id, {}
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "010")])
        _, section_id = self.get_object_reference(
            "som_switching", "atc_section_factura"
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name, u"R per defecte expedient")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, False)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        model, id = ref.step_ids[0].pas_id.split(",")
        self.assertEqual(model, "giscedata.switching.r1.01")
        model_obj = self.get_model(model)
        pas = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(pas.subtipus_id.id, subtipus_id)
        self.assertEqual(pas.reclamacio_ids[0].num_factura, '1234567890ABCD')
        txt_file = get_module_resource('som_autoreclama', 'data', 'R1-01-010-legal_text.txt')
        with open(txt_file, 'r') as f:
            legal_txt = f.read()
        self.assertEqual(pas.comentaris, legal_txt)

    def test_create_ATC_R1_010_from_f1_via_wizard__f1_C_line_frau(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '11',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })

        new_atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
            self.cursor, self.uid, f1_id, {}
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "010")])
        _, section_id = self.get_object_reference(
            "som_switching", "atc_section_factura"
        )

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name, u"R per defecte expedient")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, False)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        model, id = ref.step_ids[0].pas_id.split(",")
        self.assertEqual(model, "giscedata.switching.r1.01")
        model_obj = self.get_model(model)
        pas = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(pas.subtipus_id.id, subtipus_id)
        self.assertEqual(pas.reclamacio_ids[0].num_factura, '1234567890ABCD')
        txt_file = get_module_resource('som_autoreclama', 'data', 'R1-01-010-legal_text.txt')
        with open(txt_file, 'r') as f:
            legal_txt = f.read()
        self.assertEqual(pas.comentaris, legal_txt)

    def test_create_ATC_R1_010_from_f1_via_wizard__f1_C_line_anomalia_x_2_repeated(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })

        new_atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
            self.cursor, self.uid, f1_id, {}
        )

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
                self.cursor, self.uid, f1_id, {}
            )

        msg = u"Error en la creació del CAC amb R1 010, ja existeix un R1 obert vinculat a la mateixa factura f1 {}".format(f1_id)  # noqa: E501
        self.assertTrue(msg in context.exception.message)

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)
        self.assertEqual(atc.name, u"R per defecte expedient")

    def test_create_ATC_R1_010_from_f1_via_wizard__f1_C_line_anomalia_x_2(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 1)

        f1A_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1A_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1A_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1A_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1A_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })

        f1B_id = f1_ids[1]
        f1 = f1_obj.browse(self.cursor, self.uid, f1B_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1B_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "9876543210ZYX",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1B_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1B_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })

        A_atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
            self.cursor, self.uid, f1A_id, {}
        )

        B_atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
            self.cursor, self.uid, f1B_id, {}
        )

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "010")])
        _, section_id = self.get_object_reference(
            "som_switching", "atc_section_factura"
        )
        txt_file = get_module_resource('som_autoreclama', 'data', 'R1-01-010-legal_text.txt')
        with open(txt_file, 'r') as f:
            legal_txt = f.read()

        atc = atc_obj.browse(self.cursor, self.uid, A_atc_id)

        self.assertEqual(atc.name, u"R per defecte expedient")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, False)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        model, id = ref.step_ids[0].pas_id.split(",")
        self.assertEqual(model, "giscedata.switching.r1.01")
        model_obj = self.get_model(model)
        pas = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(pas.subtipus_id.id, subtipus_id)
        self.assertEqual(pas.reclamacio_ids[0].num_factura, '1234567890ABCD')
        self.assertEqual(pas.comentaris, legal_txt)

        atc = atc_obj.browse(self.cursor, self.uid, B_atc_id)

        self.assertEqual(atc.name, u"R per defecte expedient")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, False)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        model, id = ref.step_ids[0].pas_id.split(",")
        self.assertEqual(model, "giscedata.switching.r1.01")
        model_obj = self.get_model(model)
        pas = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(pas.subtipus_id.id, subtipus_id)
        self.assertEqual(pas.reclamacio_ids[0].num_factura, '9876543210ZYX')
        self.assertEqual(pas.comentaris, legal_txt)


class SomAutoreclamaEzATC_Test(SomAutoreclamaBaseTests):
    def build_atc(
        self,
        subtype="029",
        r1=False,
        channel="intercambi",
        section="client",
        log_days=3,
        agent_actual="10",
        state="pending",
        active=True,
        date_closed=None,
        date=None,
    ):
        atc_obj = self.get_model("giscedata.atc")
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0002"
        )

        par1_id = self.search_in("res.partner", [("name", "ilike", "Tiny sprl")])
        par2_id = self.search_in("res.partner", [("name", "ilike", "ASUStek")])
        par_obj = self.get_model("res.partner")
        par_obj.write(self.cursor, self.uid, par1_id, {"ref": "58264"})
        par_obj.write(self.cursor, self.uid, par2_id, {"ref": "58265"})

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", channel)])
        section_id = self.search_in("crm.case.section", [("name", "ilike", section)])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", subtype)])

        new_case_data = {
            "polissa_id": polissa_id,
            "descripcio": u"Reclamació per retràs automàtica",
            "canal_id": channel_id,
            "section_id": section_id,
            "subtipus_reclamacio_id": subtipus_id,
            "comentaris": u"test test test",
            "sense_responsable": True,
            "tanca_al_finalitzar_r1": r1,
            "crear_cas_r1": r1,
        }
        atc_id = atc_obj.create_general_atc_r1_case_via_wizard(
            self.cursor, self.uid, new_case_data, {}
        )
        last_write = {
            "agent_actual": agent_actual,
            "state": state,
            "active": active,
        }
        if date:
            last_write['date'] = date
        atc_obj.write(
            self.cursor,
            self.uid,
            atc_id,
            last_write,
        )
        if date_closed:
            atc_obj.write(
                self.cursor,
                self.uid,
                atc_id,
                {'date_closed': date_closed}
            )
        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        log_obj = self.get_model("crm.case.log")
        log_obj.write(self.cursor, self.uid, atc.log_ids[1].id, {"date": today_minus_str(log_days)})

        return atc_id

    def build_polissa(
        self,
        name="polissa_0002",
        f1_date_days_from_today=None,
        initial_state=None,
        data_baixa=None,
        data_baixa_from_today=None,
    ):
        f1i_obj = self.get_model("giscedata.polissa.f1.info")
        h_obj = self.get_model("som.autoreclama.state.history.polissa")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", name
        )

        if f1_date_days_from_today is not None:
            date = today_minus_str(f1_date_days_from_today)
            f1i_obj.create(
                self.cursor,
                self.uid,
                {
                    'polissa_id': polissa_id,
                    'data_ultima_lectura_f1': date,
                }
            )

        states = {
            'correct': "correct_state_workflow_polissa",
            'loop': "loop_state_workflow_polissa",
            'disabled': "disabled_state_workflow_polissa",
        }
        if initial_state in states:
            _, st_id = self.get_object_reference(
                "som_autoreclama",
                states[initial_state]
            )
            h_obj.historize(
                self.cursor, self.uid,
                polissa_id,
                st_id,
                None,
                None
            )

        par1_id = self.search_in("res.partner", [("name", "ilike", "Tiny sprl")])
        par2_id = self.search_in("res.partner", [("name", "ilike", "ASUStek")])
        par_obj = self.get_model("res.partner")
        par_obj.write(self.cursor, self.uid, par1_id, {"ref": "58264"})
        par_obj.write(self.cursor, self.uid, par2_id, {"ref": "58265"})

        pol_obj = self.get_model("giscedata.polissa")
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        if data_baixa_from_today:
            data_baixa = today_minus_str(data_baixa_from_today)

        if data_baixa is not None:
            vals = {"data_baixa": data_baixa}
            if data_baixa:
                vals['state'] = 'baixa'

            pol_obj.write(self.cursor, self.uid, polissa_id, vals)

        return polissa_id

    def add_done_006_to_polissa(self, pol_id, days):
        dat = today_minus_str(days)
        return self.build_atc(subtype="006", state='done', date_closed=dat, date=dat, r1=False)

    def add_correct_to_history(self, pol_id, days, atc_id=None):
        imd_obj = self.get_model("ir.model.data")
        polh_obj = self.get_model("som.autoreclama.state.history.polissa")
        correct_state_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_autoreclama", "correct_state_workflow_polissa"
        )[1]
        polh_obj.historize(
            self.cursor, self.uid, pol_id, correct_state_id, today_minus_str(days), atc_id)

    def add_review_to_history(self, pol_id, days, atc_id=None):
        imd_obj = self.get_model("ir.model.data")
        polh_obj = self.get_model("som.autoreclama.state.history.polissa")
        review_state_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_autoreclama", "review_state_workflow_polissa"
        )[1]
        polh_obj.historize(
            self.cursor, self.uid, pol_id, review_state_id, today_minus_str(days), atc_id)


class SomAutoreclamaConditionsTest(SomAutoreclamaEzATC_Test):
    def test_fit_atc_condition__001_c_no(self):
        atc_obj = self.get_model("giscedata.atc")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        atc_id = self.build_atc(subtype="001", log_days=10)
        atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})

        _, cond_id = self.get_object_reference(
            "som_autoreclama", "conditions_001_correct_state_workflow_atc"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, atc_data, "atc", {})
        self.assertEqual(ok, False)

    def test_fit_atc_condition__001_c_yes(self):
        atc_obj = self.get_model("giscedata.atc")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        atc_id = self.build_atc(subtype="001", log_days=50, r1=True)
        atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})

        _, cond_id = self.get_object_reference(
            "som_autoreclama", "conditions_001_correct_state_workflow_atc"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, atc_data, "atc", {})
        self.assertEqual(ok, True)

    def test_fit_atc_condition__some(self):
        atc_obj = self.get_model("giscedata.atc")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        test_datas = [
            {
                "subtype": "001",
                "log_days": 30 / 2,
                "result": False,
                "cond": "conditions_001_correct_state_workflow_atc",
            },
            {
                "subtype": "001",
                "log_days": 30 * 2,
                "result": True,
                "cond": "conditions_001_correct_state_workflow_atc",
            },
            {
                "subtype": "038",
                "log_days": 30 / 2,
                "result": False,
                "cond": "conditions_038_correct_state_workflow_atc",
            },
            {
                "subtype": "038",
                "log_days": 30 * 2,
                "result": True,
                "cond": "conditions_038_correct_state_workflow_atc",
            },
            {
                "subtype": "027",
                "log_days": 10 / 2,
                "result": False,
                "cond": "conditions_027_correct_state_workflow_atc",
            },
            {
                "subtype": "027",
                "log_days": 10 * 2,
                "result": True,
                "cond": "conditions_027_correct_state_workflow_atc",
            },
            {
                "subtype": "039",
                "log_days": 30 / 2,
                "result": False,
                "cond": "conditions_039_correct_state_workflow_atc",
            },
            {
                "subtype": "039",
                "log_days": 30 * 2,
                "result": True,
                "cond": "conditions_039_correct_state_workflow_atc",
            },
        ]

        for test_data in test_datas:
            atc_id = self.build_atc(
                subtype=test_data["subtype"], log_days=test_data["log_days"], r1=True
            )
            atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})

            _, cond_id = self.get_object_reference(
                "som_autoreclama", test_data["cond"]
            )

            ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, atc_data, "atc", {})
            self.assertEqual(ok, test_data["result"])

    def test_fit_atc_condition__all(self):
        atc_obj = self.get_model("giscedata.atc")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        cond_ids = cond_obj.search(self.cursor, self.uid, [('subtype_id', '!=', False)])
        for cond_id in cond_ids:
            cond = cond_obj.browse(self.cursor, self.uid, cond_id)

            print(cond.subtype_id.name)
            if cond.subtype_id.name == "006":  # unsuported
                continue

            # test more
            atc_id = self.build_atc(subtype=cond.subtype_id.name, log_days=cond.days * 2, r1=True)
            atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})
            ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, atc_data, "atc", {})
            self.assertEqual(ok, True, "Error on More than for condition id {}".format(cond_id))

            # test less
            atc_id = self.build_atc(subtype=cond.subtype_id.name, log_days=cond.days / 2, r1=True)
            atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})
            ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, atc_data, "atc", {})
            self.assertEqual(ok, False, "Error on Less than for condition id {}".format(cond_id))

    def test_fit_polissa_condition__noF1_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        pol_id = self.build_polissa(f1_date_days_from_today=75 + 1)
        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, {})

        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_days_since_last_f1_correct_state_workflow_polissa"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__noF1_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        pol_id = self.build_polissa(f1_date_days_from_today=75)
        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, {})

        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_days_since_last_f1_correct_state_workflow_polissa",
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__F1ok_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        pol_id = self.build_polissa(f1_date_days_from_today=60)
        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, {})

        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_receive_f1_loop_state_workflow_polissa"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__F1ok_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        pol_id = self.build_polissa(f1_date_days_from_today=61)
        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, {})

        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_receive_f1_loop_state_workflow_polissa"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__2_006_in_a_row_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1006': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_006_to_polissa(pol_id, 85)
        atc2_id = self.add_done_006_to_polissa(pol_id, 80)
        self.add_correct_to_history(pol_id, 85, atc1_id)
        self.add_correct_to_history(pol_id, 80, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_correct_2_006_inarow_review_state_workflow_polissa"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__2_006_in_a_row_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1006': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)

        atc1_id = self.add_done_006_to_polissa(pol_id, 85)
        atc2_id = self.add_done_006_to_polissa(pol_id, 20)
        self.add_correct_to_history(pol_id, 85, atc1_id)
        self.add_correct_to_history(pol_id, 20, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_correct_2_006_inarow_review_state_workflow_polissa"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__2_006_in_a_row_with_previous_review_state_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1006': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_006_to_polissa(pol_id, 85)
        atc2_id = self.add_done_006_to_polissa(pol_id, 80)
        self.add_review_to_history(pol_id, 90)
        self.add_correct_to_history(pol_id, 85, atc1_id)
        self.add_correct_to_history(pol_id, 80, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_correct_2_006_inarow_review_state_workflow_polissa"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__2_006_in_a_row_with_previous_review_state_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1006': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_006_to_polissa(pol_id, 85)
        atc2_id = self.add_done_006_to_polissa(pol_id, 80)
        self.add_correct_to_history(pol_id, 85, atc1_id)
        self.add_review_to_history(pol_id, 82)
        self.add_correct_to_history(pol_id, 80, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(self.cursor, self.uid, pol_id, context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_correct_2_006_inarow_review_state_workflow_polissa"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa", {})
        self.assertEqual(ok, False)


class SomAutoreclamaUpdaterTest(SomAutoreclamaEzATC_Test):
    def test_get_atc_candidates_to_update__all(self):
        atc_ids = []

        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        atcs = updtr_obj.get_atc_candidates_to_update(self.cursor, self.uid)

        self.assertEqual(set(atc_ids) & set(atcs), set(atc_ids))
        self.assertTrue(len(atcs) >= 7)

    def test_get_atc_candidates_to_update__none(self):
        atc_ids = []

        atc_ids.append(self.build_atc(active=False))
        atc_ids.append(self.build_atc(state="open"))
        atc_ids.append(self.build_atc(agent_actual="06"))
        atc_ids.append(self.build_atc())
        state_d_id = self.search_in("som.autoreclama.state", [("name", "ilike", "desact")])
        history_obj = self.get_model("som.autoreclama.state.history.atc")
        history_obj.historize(self.cursor, self.uid, atc_ids[-1], state_d_id, today_str(), False)

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        atcs = updtr_obj.get_atc_candidates_to_update(self.cursor, self.uid)

        self.assertEqual(set(atcs), set())

    def test_get_atc_candidates_to_update__some(self):
        atc_ids = []

        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc(active=False))
        atc_ids.append(self.build_atc(state="open"))
        atc_ids.append(self.build_atc(agent_actual="06"))
        atc_ids.append(self.build_atc())
        state_d_id = self.search_in("som.autoreclama.state", [("name", "ilike", "desact")])
        history_obj = self.get_model("som.autoreclama.state.history.atc")
        history_obj.historize(self.cursor, self.uid, atc_ids[-1], state_d_id, today_str(), False)

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        atcs = updtr_obj.get_atc_candidates_to_update(self.cursor, self.uid)

        self.assertEqual(set(atc_ids[:2]) & set(atcs), set(atc_ids[:2]))
        self.assertEqual(set(atc_ids[2:]) & set(atcs), set())
        self.assertTrue(len(atcs) >= 2)

    def test_update_atc_if_possible__no_condition_meet(self):
        atc_id = self.build_atc()

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, atc_id, "atc", {})

        self.assertEqual(status, False)
        self.assertTrue(message.startswith(u"No compleix cap condici\xf3 activa, examinades "))
        self.assertTrue(message.endswith(u"condicions."))
        self.assertTrue(int(message[44:46]) >= 59)

    def test_update_atc_if_possible__do_action_test(self):
        self.get_model("giscedata.atc")

        atc_id = self.build_atc(log_days=60, subtype="001", r1=True)

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, atc_id, "atc", {"search_only": True}
        )

        self.assertEqual(status, True)
        self.assertEqual(message, u"Testing")

    def test_update_atc_if_possible__do_action_full(self):
        atc_obj = self.get_model("giscedata.atc")

        atc_id = self.build_atc(log_days=60, subtype="001", r1=True)

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, atc_id, "atc", {})

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Primera reclamacio executat, nou atc creat amb id ")
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        self.assertGreaterEqual(atc.business_days_with_same_agent, 30)
        self.assertEqual(atc.agent_actual, u"10")
        self.assertEqual(atc.autoreclama_state.name, u"Primera reclamacio")
        self.assertEqual(atc.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(atc.autoreclama_history_ids), 2)

    def test_update_atcs_if_possible__some_consitions(self):
        atc_n_id = self.build_atc(r1=True)
        atc_y_id = self.build_atc(log_days=60, subtype="001", r1=True)

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        up, not_up, error, msg, s = updtr_obj.update_items_if_possible(
            self.cursor, self.uid, [atc_y_id, atc_n_id], "atc", True, {}
        )

        self.assertEqual(up, [atc_y_id])
        self.assertEqual(not_up, [atc_n_id])
        self.assertEqual(error, [])

    def _WIP_test_get_polissa_candidates_to_update__all(self):
        pol_ids = []

        pol_ids.append(self.build_polissa(name="polissa_0001", f1_date_days_from_today=10))
        pol_ids.append(self.build_polissa(name="polissa_0002", f1_date_days_from_today=24))
        pol_ids.append(self.build_polissa(name="polissa_0003", f1_date_days_from_today=15))
        pol_ids.append(self.build_polissa(name="polissa_0004", f1_date_days_from_today=16))
        pol_ids.append(self.build_polissa(name="polissa_0005", f1_date_days_from_today=22))

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        pols = updtr_obj.get_polissa_candidates_to_update(self.cursor, self.uid)

        self.assertEqual(set(pol_ids) & set(pols), set(pol_ids))
        self.assertTrue(len(pols) >= 5)

    def test_update_polissa_if_possible__on_correct__no_condition_meet(self):
        pol_id = self.build_polissa(
            f1_date_days_from_today=24,
            initial_state='correct',
            data_baixa=False,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, False)
        self.assertTrue(message.startswith(u"No compleix cap condici\xf3 activa, examinades "))
        self.assertTrue(message.endswith(u"condicions."))
        self.assertTrue(int(message[44:46]) >= 1)
        self.assertEqual(cnd_id, None)

    def test_update_polissa_if_possible__on_correct__nof1__do_action_test(self):
        pol_id = self.build_polissa(
            f1_date_days_from_today=75 + 1,
            initial_state='correct',
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {"search_only": True}
        )

        self.assertEqual(status, True)
        self.assertEqual(message, u"Testing")
        self.assertEqual(cnd_id, None)

    def test_update_polissa_if_possible__on_correct__nof1__do_action_full(self):
        pol_obj = self.get_model("giscedata.polissa")

        pol_id = self.build_polissa(
            f1_date_days_from_today=75 + 1,
            initial_state='correct',
            data_baixa=False,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Reclamació Bucle executat, nou atc creat amb id ")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Reclamació Bucle")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_days_since_last_f1_correct_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

    def test_update_polissa_if_possible__on_correct__baixa_facturada__do_action_full(self):
        pol_obj = self.get_model("giscedata.polissa")
        pol_id = self.build_polissa(
            f1_date_days_from_today=75 + 1,
            initial_state='correct',
            data_baixa_from_today=200,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Desactivat - Gestió Manual sense acció --> Ok")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Desactivat - Gestió Manual")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_old_polissa_correct_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

    def test_update_polissa_if_possible__on_correct__old__do_action_full(self):
        pol_obj = self.get_model("giscedata.polissa")
        pol_id = self.build_polissa(
            f1_date_days_from_today=369,
            initial_state='correct',
            data_baixa_from_today=366,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Desactivat - Gestió Manual sense acció --> Ok")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Desactivat - Gestió Manual")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_old_polissa_correct_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

    def test_update_polissa_if_possible__on_correct__nothing__do_action(self):
        pol_obj = self.get_model("giscedata.polissa")
        pol_id = self.build_polissa(
            f1_date_days_from_today=75,
            initial_state='correct',
            data_baixa_from_today=74,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, False)
        self.assertTrue(
            message.startswith(u"No compleix cap condició activa, examinades")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Correcte")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 1)
        self.assertEqual(cnd_id, None)

    def test_update_polissa_if_possible__on_correct__review__do_action(self):
        pol_obj = self.get_model("giscedata.polissa")
        pol_id = self.build_polissa(
            f1_date_days_from_today=75 + 1,
            initial_state='correct',
            data_baixa=False,
        )

        atc1_id = self.add_done_006_to_polissa(pol_id, 85)
        atc2_id = self.add_done_006_to_polissa(pol_id, 80)
        self.add_correct_to_history(pol_id, 85, atc1_id)
        self.add_correct_to_history(pol_id, 80, atc2_id)

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Revisar executat")
        )
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_correct_2_006_inarow_review_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Revisar")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2 + 1)

        text = pol.info_gestio_endarrerida.split("/n")[0]
        self.assertEqual(text[:10], today_str())
        self.assertEqual(text[20:], "Autoreclama passat a estat 'Revisar'")

    def test_update_polissa_if_possible__on_correct__nof1_review_between__do_action_full(self):
        pol_obj = self.get_model("giscedata.polissa")

        pol_id = self.build_polissa(
            f1_date_days_from_today=75 + 1,
            initial_state='correct',
            data_baixa=False,
        )
        atc1_id = self.add_done_006_to_polissa(pol_id, 85)
        atc2_id = self.add_done_006_to_polissa(pol_id, 80)
        self.add_correct_to_history(pol_id, 85, atc1_id)
        self.add_review_to_history(pol_id, 82)
        self.add_correct_to_history(pol_id, 80, atc2_id)

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Reclamació Bucle executat, nou atc creat amb id ")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Reclamació Bucle")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_days_since_last_f1_correct_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

    def test_update_polissa_if_possible__on_loop__f1ok__do_action_full_back(self):
        pol_obj = self.get_model("giscedata.polissa")

        pol_id = self.build_polissa(
            f1_date_days_from_today=30,
            initial_state='loop',
            data_baixa=False,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Correcte sense acció --> Ok")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Correcte")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_receive_f1_loop_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

    def test_update_polissa_if_possible__on_loop__again__do_action_full_loop(self):
        pol_obj = self.get_model("giscedata.polissa")

        pol_id = self.build_polissa(
            f1_date_days_from_today=30,
            initial_state='loop',
        )

        mock_funcion = mock.Mock(return_value={
            'days_without_F1': 61,
            'days_since_current_CACR1006_closed': 21,
            'days_since_baixa': 0,
            'baixa_facturada': False,
            'CACR1006s_in_last_conf_days': 1,
        })
        with mock.patch(
            'som_autoreclama.giscedata_polissa.GiscedataPolissa.get_autoreclama_data',
            mock_funcion
        ):
            updtr_obj = self.get_model("som.autoreclama.state.updater")
            status, cnd_id, message = updtr_obj.update_item_if_possible(
                self.cursor, self.uid, pol_id, "polissa", {}
            )
            self.assertEqual(status, True)
            self.assertTrue(
                message.startswith(u"Estat Reclamaci\xf3 Bucle executat, nou atc creat amb id ")
            )
            pol = pol_obj.browse(self.cursor, self.uid, pol_id)
            self.assertEqual(pol.autoreclama_state.name, u"Reclamació Bucle")
            self.assertEqual(pol.autoreclama_state_date, today_str())
            self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
            _, expected_ncd_id = self.get_object_reference(
                "som_autoreclama",
                "conditions_CACR1006_closed_loop_state_workflow_polissa"
            )
            self.assertEqual(cnd_id, expected_ncd_id)

    def test_update_polissa_if_possible__on_loop__continue__do_action_full_stay(self):
        pol_obj = self.get_model("giscedata.polissa")

        pol_id = self.build_polissa(
            f1_date_days_from_today=30,
            initial_state='loop',
        )

        mock_funcion = mock.Mock(return_value={
            'days_without_F1': 61,
            'days_since_current_CACR1006_closed': 20,
            'days_since_baixa': 0,
            'baixa_facturada': False,
            'CACR1006s_in_last_conf_days': 1,
        })
        with mock.patch(
            'som_autoreclama.giscedata_polissa.GiscedataPolissa.get_autoreclama_data',
            mock_funcion
        ):
            updtr_obj = self.get_model("som.autoreclama.state.updater")
            status, cnd_id, message = updtr_obj.update_item_if_possible(
                self.cursor, self.uid, pol_id, "polissa", {}
            )
            self.assertEqual(status, False)
            self.assertTrue(
                message.startswith(u"No compleix cap condici\xf3 activa, examinades ")
            )
            pol = pol_obj.browse(self.cursor, self.uid, pol_id)
            self.assertEqual(pol.autoreclama_state.name, u"Reclamació Bucle")
            self.assertEqual(pol.autoreclama_state_date, today_str())
            self.assertGreaterEqual(len(pol.autoreclama_history_ids), 1)
            self.assertEqual(cnd_id, None)

    def test_update_polissa_if_possible__on_loop__baixa__do_action(self):
        pol_obj = self.get_model("giscedata.polissa")
        pol_id = self.build_polissa(
            f1_date_days_from_today=75 + 1,
            initial_state='loop',
            data_baixa_from_today=200,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Desactivat - Gestió Manual sense acció --> Ok")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Desactivat - Gestió Manual")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_old_polissa_loop_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

    def test_update_polissa_if_possible__on_loop__facturada__do_action(self):
        pol_obj = self.get_model("giscedata.polissa")
        pol_id = self.build_polissa(
            f1_date_days_from_today=369,
            initial_state='loop',
            data_baixa_from_today=366,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Desactivat - Gestió Manual sense acció --> Ok")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Desactivat - Gestió Manual")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_old_polissa_loop_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

    def test_update_polissa_if_possible__on_loop__reloop__do_action(self):
        pol_obj = self.get_model("giscedata.polissa")
        atc_obj = self.get_model("giscedata.atc")
        sw_obj = self.get_model("giscedata.switching")

        pol_id = self.build_polissa(
            f1_date_days_from_today=75 + 1,
            initial_state='correct',
            data_baixa=False,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Reclamació Bucle executat, nou atc creat amb id ")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Reclamació Bucle")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 2)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_days_since_last_f1_correct_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)

        first_006 = pol.autoreclama_history_ids[0]['generated_atc_id']

        # unlock the R1 and the ATC
        r1 = self.browse_referenced(first_006.ref)
        sw_obj.write(self.cursor, self.uid, r1.id, {
            "ref": '',
            "state": 'done',
        })
        atc_obj.write(self.cursor, self.uid, first_006.id, {
            "ref": '',
        })

        # close the ATC and set it up
        atc_obj.write(self.cursor, self.uid, first_006.id, {
            "state": 'done'
        })
        data_close = today_minus_str(21)
        atc_obj.write(self.cursor, self.uid, first_006.id, {
            "date_closed": data_close
        })

        # The real test
        status, cnd_id, message = updtr_obj.update_item_if_possible(
            self.cursor, self.uid, pol_id, "polissa", {}
        )

        self.assertEqual(status, True)
        self.assertTrue(
            message.startswith(u"Estat Reclamació Bucle executat, nou atc creat amb id ")
        )

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.name, u"Reclamació Bucle")
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(pol.autoreclama_history_ids), 3)
        _, e_cnd_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_CACR1006_closed_loop_state_workflow_polissa"
        )
        self.assertEqual(cnd_id, e_cnd_id)
        second_006_id = pol.autoreclama_history_ids[0]['generated_atc_id'].id
        self.assertNotEqual(first_006.id, second_006_id)

    def test_update_polisses_if_possible__some_conditions(self):
        pol_n_id = self.build_polissa(
            name="polissa_0003",
            f1_date_days_from_today=24,
            initial_state='correct',
            data_baixa=False,
        )

        pol_y_id = self.build_polissa(
            name="polissa_0002",
            f1_date_days_from_today=30,
            initial_state='loop',
            data_baixa=False,
        )

        updtr_obj = self.get_model("som.autoreclama.state.updater")
        up, not_up, error, msg, s = updtr_obj.update_items_if_possible(
            self.cursor, self.uid, [pol_y_id, pol_n_id], "polissa", True, {}
        )

        self.assertEqual(up, [pol_y_id])
        self.assertEqual(not_up, [pol_n_id])
        self.assertEqual(error, [])


class SomAutoreclamaDoActionTest(SomAutoreclamaEzATC_Test):
    def test_do_action__deactivated(self):
        atc_obj = self.get_model("giscedata.atc")
        state_obj = self.get_model("som.autoreclama.state")

        atc_id = self.build_atc(log_days=60, subtype="001")

        _, state_id = self.get_object_reference(
            "som_autoreclama", "disabled_state_workflow_atc"
        )
        state_obj.write(self.cursor, self.uid, state_id, {"active": False})
        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, "atc", {})

        self.assertEqual(result["do_change"], False)
        self.assertEqual(result["message"], u"Estat {} desactivat!".format(state.name))
        self.assertTrue("created_atc" not in result)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)  # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))

    def test_do_action__no_action(self):
        atc_obj = self.get_model("giscedata.atc")
        state_obj = self.get_model("som.autoreclama.state")

        atc_id = self.build_atc(log_days=60, subtype="001")

        _, state_id = self.get_object_reference(
            "som_autoreclama", "correct_state_workflow_atc"
        )
        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, "atc", {})

        self.assertEqual(result["do_change"], True)
        self.assertEqual(result["message"], u"Estat {} sense acció --> Ok".format(state.name))
        self.assertTrue("created_atc" not in result)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)  # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))

    def test_do_action__ok(self):
        atc_obj = self.get_model("giscedata.atc")
        state_obj = self.get_model("som.autoreclama.state")

        atc_id = self.build_atc(log_days=60, subtype="001", r1=True)

        _, state_id = self.get_object_reference(
            "som_autoreclama", "first_state_workflow_atc"
        )
        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, "atc", {})

        self.assertEqual(result["do_change"], True)
        self.assertEqual(
            result["message"],
            u"Estat {} executat, nou atc creat amb id {}".format(state.name, result["created_atc"]),
        )
        self.assertGreaterEqual(result["created_atc"], atc_id)
        new_atc_id = result["created_atc"]

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)  # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))

        atc_obj.browse(self.cursor, self.uid, new_atc_id)
        # automated atc creation covered by test_create_ATC_R1_029_from_atc_via_wizard__from_atr

    def test_do_action__error(self):
        atc_obj = self.get_model("giscedata.atc")
        state_obj = self.get_model("som.autoreclama.state")

        atc_id = self.build_atc(log_days=60, subtype="001")

        _, state_id = self.get_object_reference(
            "som_autoreclama", "first_state_workflow_atc"
        )
        state_obj.write(
            self.cursor,
            self.uid,
            state_id,
            {
                "generate_atc_parameters_text": '{"model": "giscedata.atc", "method": "create_ATC_R1_029_from_atc_via_wizard_ERROR"}',  # noqa: E501
            },
        )

        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, "atc", {})

        self.assertEqual(result["do_change"], False)
        self.assertTrue(
            result["message"].startswith(
                u"Execuci\xf3 d'accions del estat {} genera ERROR".format(state.name)
            )
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)  # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))


class SomAutoreclamaf1cAutomationTest(SomAutoreclamaEzATC_Test):
    def test__get_f1c_candidates_to_reclaim__find_none(self):
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        f1_ids = aut_obj.get_f1c_candidates_to_reclaim(self.cursor, self.uid, {})

        self.assertEqual(len(f1_ids), 0)

    def test__get_f1c_candidates_to_reclaim__find_one_c(self):
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        f1_ids = f1_obj.search(self.cursor, self.uid, [])
        self.assertGreater(len(f1_ids), 1)
        f1_id = f1_ids[0]

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "type_factura": "C",
        })
        last_hours = (datetime.now() - timedelta(hours=120)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        found_ids = aut_obj.get_f1c_candidates_to_reclaim(self.cursor, self.uid, {})

        self.assertEqual(len(found_ids), 0)

        last_hours = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        found_ids = aut_obj.get_f1c_candidates_to_reclaim(self.cursor, self.uid, {})

        self.assertEqual(len(found_ids), 1)
        self.assertEqual(found_ids[0], f1_id)

    def test__get_f1c_candidates_to_reclaim__find_one_c_already_reclaimed(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        new_atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
            self.cursor, self.uid, f1_id, {}
        )

        found_ids = aut_obj.get_f1c_candidates_to_reclaim(self.cursor, self.uid, {})

        self.assertTrue(f1_id in found_ids)

        atc_obj.write(self.cursor, self.uid, new_atc_id, {
            'description': u"cosa {} mes cosa {} altre cosa.".format(
                aut_obj.tag,
                f1.invoice_number_text,
            )
        })

        found_ids = aut_obj.get_f1c_candidates_to_reclaim(self.cursor, self.uid, {})

        self.assertTrue(f1_id not in found_ids)

    def test__reclaim_f1c__none(self):
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        ok, error, msg = aut_obj.reclaim_f1c(self.cursor, self.uid, [], {})

        self.assertEqual(len(ok), 0)
        self.assertEqual(len(error), 0)
        self.assertEqual(msg, u"Sumari ATC 010 per F1 tipus C\nF1's tipus C amb ATC generat : .................... 0\nF1's tipus C que han donat error en generar ATC ....0\n\n")  # noqa: E501

    def test__reclaim_f1c__not_c_type(self):
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        f1_ids = f1_obj.search(self.cursor, self.uid, [])
        self.assertGreater(len(f1_ids), 1)
        f1_id = f1_ids[0]

        ok, error, msg = aut_obj.reclaim_f1c(self.cursor, self.uid, [f1_id], {})

        self.assertEqual(len(ok), 0)
        self.assertEqual(len(error), 1)
        self.assertTrue("F1's tipus C amb ATC generat : .................... 0" in msg)
        self.assertTrue("F1's tipus C que han donat error en generar ATC ....1" in msg)
        exce = u"Error en la creació del CAC amb R1 010, F1 no es tipus C id_f1 {}".format(error[0])
        self.assertTrue(exce in msg)

    def test__reclaim_f1c__no_lines(self):
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        f1_ids = f1_obj.search(self.cursor, self.uid, [])
        self.assertGreater(len(f1_ids), 1)
        f1_id = f1_ids[0]
        f1_obj.write(self.cursor, self.uid, f1_id, {
            "type_factura": "C",
        })

        ok, error, msg = aut_obj.reclaim_f1c(self.cursor, self.uid, [f1_id], {})

        self.assertEqual(len(ok), 0)
        self.assertEqual(len(error), 1)
        self.assertTrue("F1's tipus C amb ATC generat : .................... 0" in msg)
        self.assertTrue("F1's tipus C que han donat error en generar ATC ....1" in msg)
        exce = u"Error en la creació del CAC amb R1 010, F1 sense linies id_f1 {}".format(error[0])
        self.assertTrue(exce in msg)

    def test__reclaim_f1c__one_ok(self):
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 1)

        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })

        ok, error, msg = aut_obj.reclaim_f1c(self.cursor, self.uid, [f1_id], {})

        self.assertEqual(len(ok), 1)
        self.assertEqual(len(error), 0)
        self.assertTrue("F1's tipus C amb ATC generat : .................... 1" in msg)
        self.assertTrue("F1's tipus C que han donat error en generar ATC ....0" in msg)
        exce = u"F1 {} ha generat cas ATC 010 amb id ".format(f1.name)
        self.assertTrue(exce in msg)

    def test__automation__none(self):
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        msg = aut_obj.automation(self.cursor, self.uid, {})

        self.assertEqual(msg, u"Sumari ATC 010 per F1 tipus C\nF1's tipus C amb ATC generat : .................... 0\nF1's tipus C que han donat error en generar ATC ....0\n\n")  # noqa: E501

    def test__automation__1_yes(self):
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 1)

        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        msg = aut_obj.automation(self.cursor, self.uid, {})

        self.assertTrue("F1's tipus C amb ATC generat : .................... 1" in msg)
        self.assertTrue("F1's tipus C que han donat error en generar ATC ....0" in msg)
        exce = u"F1 {} ha generat cas ATC 010 amb id ".format(f1.name)
        self.assertTrue(exce in msg)

    def test__automation__2_yes_1_no(self):
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 2)

        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        f1_id = f1_ids[1]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "987654321ZXY",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '11',
            'importacio_id': 2,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 2,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        f1_id = f1_ids[2]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "NONONONONONONNONONNONO123",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '05',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        msg = aut_obj.automation(self.cursor, self.uid, {})

        self.assertTrue("F1's tipus C amb ATC generat : .................... 2" in msg)
        self.assertTrue("F1's tipus C que han donat error en generar ATC ....1" in msg)
        exce = u" ha generat cas ATC 010 amb id "
        self.assertTrue(exce in msg)
        exce = u"Error en la creació del CAC amb R1 010, F1 no es tipus anomalia o frau"
        self.assertTrue(exce in msg)

    def test__automation__1_yes_1_no_1_far(self):
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")
        aut_obj = self.get_model("som.autoreclama.f1c.automation")

        self.create_tags()
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {"state": 'activa'})
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 2)

        # F1 ok
        f1_id = f1_ids[0]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 1,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 1,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        # F1 far
        f1_id = f1_ids[1]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "546372819OOOOPPPSSSS",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '06',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 2,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 2,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=56)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        # F1 no ok (tipus 05)
        f1_id = f1_ids[2]
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "fecha_factura_desde": "2015-01-01",
            "invoice_number_text": "NONONONONONONNONONNONO123",
            "type_factura": "C",
        })
        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.polissa_id.id, pol.id)
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
        })
        last_hours = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        ssql = '''update giscedata_facturacio_importacio_linia set create_date = %s where id = %s'''
        self.cursor.execute(ssql, (last_hours, f1_id,))

        msg = aut_obj.automation(self.cursor, self.uid, {})

        self.assertTrue("F1's tipus C amb ATC generat : .................... 1" in msg)
        self.assertTrue("F1's tipus C que han donat error en generar ATC ....1" in msg)
        exce = u" ha generat cas ATC 010 amb id "
        self.assertTrue(exce in msg)
        exce = u"Error en la creació del CAC amb R1 010, F1 no es tipus anomalia o frau id_f1"
        self.assertTrue(exce in msg)
