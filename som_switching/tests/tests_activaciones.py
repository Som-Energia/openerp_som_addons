# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from tools.misc import cache
import mock
from addons import get_module_resource
from datetime import datetime
from destral.patch import PatchNewCursors
from osv import osv


class GiscedataSwitching(osv.osv):

    _name = "giscedata.switching"
    _inherit = "giscedata.switching"

    def importar_xml(self, cursor, uid, data, fname, context=None):
        if not context:
            context = {}
        with PatchNewCursors():
            res = super(GiscedataSwitching, self).importar_xml(cursor, uid, data, fname, context)
        return res


GiscedataSwitching()


class TestsAutoActiva(testing.OOTestCase):
    def setUp(self):
        fact_obj = self.model("giscedata.facturacio.factura")
        self.model("giscedata.facturacio.factura.linia")
        warn_obj = self.model("giscedata.facturacio.validation.warning.template")
        self.txn = Transaction().start(self.database)

        cursor = self.txn.cursor
        uid = self.txn.user

        self.malditas_tarifas_contatibles(cursor, uid)

        for fact_id in fact_obj.search(cursor, uid, []):
            fact_obj.write(cursor, uid, [fact_id], {"state": "open"})

        # We make sure that all warnings are active
        warn_ids = warn_obj.search(cursor, uid, [], context={"active_test": False})
        warn_obj.write(cursor, uid, warn_ids, {"active": True})

    def tearDown(self):
        self.txn.stop()

    def malditas_tarifas_contatibles(self, cursor, uid):
        """
        Hace a todas las tarifas compatibles con todas las listas de
        precios
        """
        tarif_obj = self.openerp.pool.get("giscedata.polissa.tarifa")
        tarifas_ids = tarif_obj.search(cursor, uid, [])
        pricelist_obj = self.openerp.pool.get("product.pricelist")
        pricelists_ids = pricelist_obj.search(cursor, uid, [])
        tarif_obj.write(
            cursor, uid, tarifas_ids, {"llistes_preus_comptatibles": [(6, 0, pricelists_ids)]}
        )

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def change_polissa_comer(self, txn):
        cursor = txn.cursor
        uid = txn.user
        imd_obj = self.openerp.pool.get("ir.model.data")
        new_comer_id = imd_obj.get_object_reference(cursor, uid, "base", "res_partner_c2c")[1]
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        pol_id = imd_obj.get_object_reference(cursor, uid, "giscedata_polissa", "polissa_0001")[1]
        pol_obj.write(cursor, uid, [pol_id], {"comercialitzadora": new_comer_id})

    def update_polissa_distri(self, txn):
        """
        Sets the distribuidora_id field in contract as the same of related cups
        """
        cursor = txn.cursor
        uid = txn.user
        imd_obj = self.openerp.pool.get("ir.model.data")

        pol_obj = self.openerp.pool.get("giscedata.polissa")
        cups_obj = self.openerp.pool.get("giscedata.cups.ps")

        contract_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0001"
        )[1]
        cups_id = pol_obj.read(cursor, uid, contract_id, ["cups"])["cups"][0]
        distri_id = cups_obj.read(cursor, uid, cups_id, ["distribuidora_id"])["distribuidora_id"][0]
        pol_obj.write(cursor, uid, contract_id, {"distribuidora": distri_id})

    @mock.patch("giscedata_switching.giscedata_switching.GiscedataSwitching.whereiam")
    def switch(
        self, txn, where, mock_function, is_autocons=False, other_id_name="res_partner_agrolait"
    ):
        cursor = txn.cursor
        uid = txn.user
        mock_function.return_value = where
        imd_obj = self.openerp.pool.get("ir.model.data")
        partner_obj = self.openerp.pool.get("res.partner")
        cups_obj = self.openerp.pool.get("giscedata.cups.ps")
        partner_id = imd_obj.get_object_reference(cursor, uid, "base", "main_partner")[1]

        other_id = imd_obj.get_object_reference(cursor, uid, "base", other_id_name)[1]
        another_id = imd_obj.get_object_reference(cursor, uid, "base", "res_partner_c2c")[1]

        if is_autocons:
            codes = {"distri": "4321", "comer": "1234"}
        else:
            codes = {"distri": "1234", "comer": "4321"}

        partner_obj.write(cursor, uid, [partner_id], {"ref": codes.pop(where)})
        partner_obj.write(cursor, uid, [other_id], {"ref": codes.values()[0]})
        partner_obj.write(cursor, uid, [another_id], {"ref": "5555"})
        cups_id = imd_obj.get_object_reference(cursor, uid, "giscedata_cups", "cups_01")[1]
        distri_ids = {"distri": partner_id, "comer": other_id}
        cups_obj.write(cursor, uid, [cups_id], {"distribuidora_id": distri_ids[where]})
        cache.clean_caches_for_db(cursor.dbname)

    def create_case_and_step(
        self, cursor, uid, contract_id, proces_name, step_name, sw_id_origin=None, context=None
    ):
        """
        Creates case and step
        :param proces_name:
        :param step_name:
        :param context:
        :return:
        """
        if context is None:
            context = {}

        if isinstance(sw_id_origin, dict):
            context = sw_id_origin
            sw_id_origin = None

        sw_obj = self.openerp.pool.get("giscedata.switching")

        swproc_obj = self.openerp.pool.get("giscedata.switching.proces")
        swpas_obj = self.openerp.pool.get("giscedata.switching.step")
        swinfo_obj = self.openerp.pool.get("giscedata.switching.step.info")
        contract_obj = self.openerp.pool.get("giscedata.polissa")

        proces_id = swproc_obj.search(cursor, uid, [("name", "=", proces_name)])[0]

        sw_params = {
            "proces_id": proces_id,
            "cups_polissa_id": contract_id,
        }

        vals = sw_obj.onchange_polissa_id(cursor, uid, [], contract_id, None, context=context)

        sw_params.update(vals["value"])
        # si no tenim ref_contracte, ens l'inventem (de moment)
        if not sw_params.get("ref_contracte", False):
            sw_params["ref_contracte"] = "111111111"

        if sw_id_origin:
            sw_id = sw_id_origin
        else:
            sw_id = sw_obj.create(cursor, uid, sw_params)

        if proces_name in ["C1", "C2"]:
            out_retail = contract_obj.read(cursor, uid, contract_id, ["comercialitzadora"])[
                "comercialitzadora"
            ][0]
            sw_obj.write(cursor, uid, sw_id, {"comer_sortint_id": out_retail})

        # creeem el pas
        pas_id = swpas_obj.get_step(cursor, uid, step_name, proces_name)
        # Creant info ja crea automaticament tota la info del pas
        info_vals = {
            "sw_id": sw_id,
            "proces_id": proces_id,
            "step_id": pas_id,
        }
        info_id = swinfo_obj.create(cursor, uid, info_vals, context=context)
        info = swinfo_obj.browse(cursor, uid, info_id)
        model_obj, model_id = info.pas_id.split(",")

        return int(model_id)

    def get_contract_id(self, txn, xml_id="polissa_0001"):
        uid = txn.user
        cursor = txn.cursor
        imd_obj = self.openerp.pool.get("ir.model.data")

        return imd_obj.get_object_reference(cursor, uid, "giscedata_polissa", xml_id)[1]

    def create_complete_case(self, polissa_id, case, step, status, substep=None):
        sw_obj = self.model("giscedata.switching")
        step_obj = self.model("giscedata.switching.{}.{}".format(case.lower(), step))

        cursor = self.txn.cursor
        uid = self.txn.user

        step_id = self.create_case_and_step(cursor, uid, polissa_id, case, step)
        step_d = step_obj.browse(cursor, uid, step_id)

        case_id = step_d.sw_id.id

        sw_obj.write(cursor, uid, step_d.sw_id.id, {"state": status})

        if substep:
            substep_obj = self.model("giscedata.subtipus.reclamacio")
            substep_ids = substep_obj.search(cursor, uid, [("name", "=", substep)])
            if substep_ids:
                step_obj.write(
                    cursor,
                    uid,
                    step_id,
                    {
                        "subtipus_id": substep_ids[0],
                    },
                )

        # refresh after modifications
        step_d = step_obj.browse(cursor, uid, step_id)
        case_d = sw_obj.browse(cursor, uid, case_id)
        return case_d, step_d

    def test_se_cierra_caso_cac_activacion_automatica_009_open(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self.switch(self.txn, "comer")

        pol_obj = self.openerp.pool.get("giscedata.polissa")
        atc_obj = self.openerp.pool.get("giscedata.atc")
        wiz_o = self.openerp.pool.get("wizard.create.atc.from.polissa")
        pol_id = self.get_contract_id(self.txn, xml_id="polissa_0001")
        pol = pol_obj.browse(cursor, uid, pol_id)
        # pol.distribuidora.write({'ref': 4444})
        # Creem un cas ATC
        ctx = {"active_ids": [pol_id], "from_model": "giscedata.polissa"}
        subtipus_id = self.openerp.pool.get("giscedata.subtipus.reclamacio").search(
            cursor, uid, [("name", "=", "009")]
        )[0]
        wiz_id = wiz_o.create(cursor, uid, {"subtipus_id": subtipus_id}, context=ctx)
        wiz_o.create_atc_case(cursor, uid, [wiz_id], pol_obj._name, ctx)
        wiz = wiz_o.browse(cursor, uid, wiz_id)
        cas = atc_obj.browse(cursor, uid, wiz.generated_cases[0])
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertEqual(cas.time_tracking_id.code, "0")
        self.assertEqual(cas.subtipus_id.name, "009")
        self.assertEqual(cas.process_step, "")

        # Cridem l'assistent de crear R1 desde ATC
        # Ha de tornar un diccionari que cridi el asistents de R1.
        # Ens quedarem amb el context i cridarem l'assistent amb aquest context
        wiz_o = self.openerp.pool.get("wizard.generate.r1.from.atc.case")
        wiz_id = wiz_o.create(cursor, uid, {}, {"active_ids": [cas.id]})
        res = wiz_o.generate_r1(cursor, uid, [wiz_id], {"active_id": cas.id})
        context = eval(dict(res).get("context", "{}"))
        extra_values = context.get("extra_values")
        self.assertEqual(extra_values["auto_r1_atc"], True)
        self.assertEqual(context["polissa_id"], pol.id)
        self.assertEqual(extra_values["ref_id"], [cas.id])
        self.assertEqual(extra_values["ref_model"], "giscedata.atc")

        # Cridem l'assistent de crear R1 amb el context obringut.
        wiz_o = self.openerp.pool.get("wizard.subtype.r1")
        wiz_id = wiz_o.create(cursor, uid, {"comentaris": "TEST"}, context)
        res = wiz_o.action_create_r1_case(cursor, uid, [wiz_id], context)
        r1_id = res.get("domain")[0][2]
        r1 = self.openerp.pool.get("giscedata.switching").browse(cursor, uid, r1_id)
        cas = atc_obj.browse(cursor, uid, cas.id)
        self.assertFalse(cas.tancar_cac_al_finalitzar_r1)
        self.assertEqual(r1.ref, "giscedata.atc, {}".format(cas.id))
        self.assertEqual(cas.ref, "giscedata.switching, {}".format(r1.id))
        self.assertEqual(cas.state, "pending")
        self.assertEqual(cas.time_tracking_id.code, "1")
        self.assertEqual(cas.process_step, "01")

        last_description = cas.history_line[0].description
        self.assertIn("R1-01 (seq. 01)", last_description)
        self.assertIn("Codi Sol.licitud: {}".format(r1.codi_sollicitud), last_description)
        self.assertIn("Data Creació:", last_description)
        self.assertIn("Comentaris: TEST", last_description)
        self.assertIn("Documents: Sense documents adjunts", last_description)
        self.assertIn(
            "Informacio Adicional: 02-009: DISCONFORMIDAD CON LECTURA FACTURADA", last_description
        )

        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r102_new.xml"
        )

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        activations_ids = act_obj.search(cursor, uid, [], context={"active_test": False})
        act_obj.write(cursor, uid, activations_ids, {"active": True, "is_automatic": True})

        imd_obj = self.openerp.pool.get("ir.model.data")

        partner_id = imd_obj.get_object_reference(cursor, uid, "base", "main_partner")[1]

        activ_custom_id = imd_obj.get_object_reference(
            cursor, uid, "som_switching", "sw_act_r105_cac"
        )[1]

        self.assertIn(activ_custom_id, activations_ids)

        sw_obj = self.model("giscedata.switching")
        sw_obj.write(cursor, uid, r1_id, {"codi_sollicitud": "201602231255"})
        # El creem ara perque la data sigui posterior a la posada al r101
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        comp_part = self.model("res.users").browse(cursor, uid, uid).company_id.partner_id

        self.assertTrue(comp_part.id == partner_id)
        self.assertTrue(comp_part.ref == "4321")

        sw_obj.importar_xml(cursor, uid, r1_xml, "r102.xml")
        res = sw_obj.search(
            cursor,
            uid,
            [
                ("proces_id.name", "=", "R1"),
                ("step_id.name", "=", "02"),
                ("codi_sollicitud", "=", "201602231255"),
            ],
        )
        self.assertEqual(len(res), 1)

        pol.write({"refacturacio_pendent": False})

        r1_05_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r105_new.xml"
        )

        data_old_05 = "<FechaSolicitud>2016-09-30T12:42:16"

        with open(r1_05_xml_path, "r") as f:
            r1_05_xml = f.read()
            data_nw = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_05_xml = r1_05_xml.replace(data_old_05, "<FechaSolicitud>{}".format(data_nw))
            r1_05_xml = r1_05_xml.replace(
                "<ResultadoReclamacion>02</ResultadoReclamacion>",
                "<ResultadoReclamacion>01</ResultadoReclamacion>",
            )
            r1_05_xml = r1_05_xml.replace("<Subtipo>013</Subtipo>", "<Subtipo>009</Subtipo>")

        cas = atc_obj.browse(cursor, uid, cas.id)

        self.assertFalse(cas.tancar_cac_al_finalitzar_r1)
        cas.write({"state": "open"})
        cas = atc_obj.browse(cursor, uid, cas.id)
        self.assertEqual(cas.state, "open")

        sw_obj.importar_xml(cursor, uid, r1_05_xml, "r105.xml")

        res = sw_obj.search(
            cursor,
            uid,
            [
                ("proces_id.name", "=", "R1"),
                ("step_id.name", "=", "05"),
                ("codi_sollicitud", "=", "201602231255"),
            ],
        )
        self.assertEqual(len(res), 1)

        cas = atc_obj.browse(cursor, uid, cas.id)
        self.assertEqual(cas.subtipus_id.name, "009")
        self.assertEqual(cas.resultat, "01")
        self.assertTrue(cas.tancar_cac_al_finalitzar_r1)
        self.assertEqual(cas.state, "done")
        r1_state = r1.read(["state"])[0]["state"]
        self.assertEqual(r1_state, "done")
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertFalse(pol.refacturacio_pendent)

    def test_se_cierra_caso_cac_activacion_automatica_009_pending(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        self.switch(self.txn, "comer")

        pol_obj = self.openerp.pool.get("giscedata.polissa")
        atc_obj = self.openerp.pool.get("giscedata.atc")
        wiz_o = self.openerp.pool.get("wizard.create.atc.from.polissa")
        pol_id = self.get_contract_id(self.txn, xml_id="polissa_0001")
        pol = pol_obj.browse(cursor, uid, pol_id)
        # pol.distribuidora.write({'ref': 4444})
        # Creem un cas ATC
        subtipus_id = self.openerp.pool.get("giscedata.subtipus.reclamacio").search(
            cursor, uid, [("name", "=", "009")]
        )[0]
        ctx = {"active_ids": [pol_id], "from_model": "giscedata.polissa"}
        wiz_id = wiz_o.create(cursor, uid, {"subtipus_id": subtipus_id}, context=ctx)
        wiz_o.create_atc_case(cursor, uid, [wiz_id], pol_obj._name, ctx)
        wiz = wiz_o.browse(cursor, uid, wiz_id)
        cas = atc_obj.browse(cursor, uid, wiz.generated_cases[0])
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertEqual(cas.time_tracking_id.code, "0")
        self.assertEqual(cas.subtipus_id.name, "009")
        self.assertEqual(cas.process_step, "")

        # Cridem l'assistent de crear R1 desde ATC
        # Ha de tornar un diccionari que cridi el asistents de R1.
        # Ens quedarem amb el context i cridarem l'assistent amb aquest context
        wiz_o = self.openerp.pool.get("wizard.generate.r1.from.atc.case")
        wiz_id = wiz_o.create(cursor, uid, {}, {"active_ids": [cas.id]})
        res = wiz_o.generate_r1(cursor, uid, [wiz_id], {"active_id": cas.id})
        context = eval(dict(res).get("context", "{}"))
        extra_values = context.get("extra_values")
        self.assertEqual(extra_values["auto_r1_atc"], True)
        self.assertEqual(context["polissa_id"], pol.id)
        self.assertEqual(extra_values["ref_id"], [cas.id])
        self.assertEqual(extra_values["ref_model"], "giscedata.atc")

        # Cridem l'assistent de crear R1 amb el context obringut.
        wiz_o = self.openerp.pool.get("wizard.subtype.r1")
        wiz_id = wiz_o.create(cursor, uid, {"comentaris": "TEST"}, context)
        res = wiz_o.action_create_r1_case(cursor, uid, [wiz_id], context)
        r1_id = res.get("domain")[0][2]
        r1 = self.openerp.pool.get("giscedata.switching").browse(cursor, uid, r1_id)
        cas = atc_obj.browse(cursor, uid, cas.id)
        self.assertFalse(cas.tancar_cac_al_finalitzar_r1)
        self.assertEqual(r1.ref, "giscedata.atc, {}".format(cas.id))
        self.assertEqual(cas.ref, "giscedata.switching, {}".format(r1.id))
        self.assertEqual(cas.state, "pending")
        self.assertEqual(cas.time_tracking_id.code, "1")
        self.assertEqual(cas.process_step, "01")

        last_description = cas.history_line[0].description
        self.assertIn("R1-01 (seq. 01)", last_description)
        self.assertIn("Codi Sol.licitud: {}".format(r1.codi_sollicitud), last_description)
        self.assertIn("Data Creació:", last_description)
        self.assertIn("Comentaris: TEST", last_description)
        self.assertIn("Documents: Sense documents adjunts", last_description)
        self.assertIn(
            "Informacio Adicional: 02-009: DISCONFORMIDAD CON LECTURA FACTURADA", last_description
        )

        data_old = "<FechaSolicitud>2016-09-29T09:39:08"
        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r102_new.xml"
        )

        act_obj = self.openerp.pool.get("giscedata.switching.activation.config")
        activations_ids = act_obj.search(cursor, uid, [], context={"active_test": False})
        act_obj.write(cursor, uid, activations_ids, {"active": True, "is_automatic": True})

        imd_obj = self.openerp.pool.get("ir.model.data")

        partner_id = imd_obj.get_object_reference(cursor, uid, "base", "main_partner")[1]

        activ_custom_id = imd_obj.get_object_reference(
            cursor, uid, "som_switching", "sw_act_r105_cac"
        )[1]

        self.assertIn(activ_custom_id, activations_ids)

        sw_obj = self.model("giscedata.switching")
        sw_obj.write(cursor, uid, r1_id, {"codi_sollicitud": "201602231255"})
        # El creem ara perque la data sigui posterior a la posada al r101
        with open(r1_xml_path, "r") as f:
            data_new = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_xml = f.read()
            r1_xml = r1_xml.replace(data_old, "<FechaSolicitud>{}".format(data_new))

        comp_part = self.model("res.users").browse(cursor, uid, uid).company_id.partner_id

        self.assertTrue(comp_part.id == partner_id)
        self.assertTrue(comp_part.ref == "4321")

        sw_obj.importar_xml(cursor, uid, r1_xml, "r102.xml")
        res = sw_obj.search(
            cursor,
            uid,
            [
                ("proces_id.name", "=", "R1"),
                ("step_id.name", "=", "02"),
                ("codi_sollicitud", "=", "201602231255"),
            ],
        )
        self.assertEqual(len(res), 1)

        pol.write({"refacturacio_pendent": False})

        r1_05_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r105_new.xml"
        )

        data_old_05 = "<FechaSolicitud>2016-09-30T12:42:16"

        with open(r1_05_xml_path, "r") as f:
            r1_05_xml = f.read()
            data_nw = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
            r1_05_xml = r1_05_xml.replace(data_old_05, "<FechaSolicitud>{}".format(data_nw))
            r1_05_xml = r1_05_xml.replace(
                "<ResultadoReclamacion>02</ResultadoReclamacion>",
                "<ResultadoReclamacion>01</ResultadoReclamacion>",
            )
            r1_05_xml = r1_05_xml.replace("<Subtipo>013</Subtipo>", "<Subtipo>009</Subtipo>")

        cas = atc_obj.browse(cursor, uid, cas.id)

        self.assertFalse(cas.tancar_cac_al_finalitzar_r1)
        cas = atc_obj.browse(cursor, uid, cas.id)
        self.assertEqual(cas.state, "pending")

        sw_obj.importar_xml(cursor, uid, r1_05_xml, "r105.xml")

        res = sw_obj.search(
            cursor,
            uid,
            [
                ("proces_id.name", "=", "R1"),
                ("step_id.name", "=", "05"),
                ("codi_sollicitud", "=", "201602231255"),
            ],
        )
        self.assertEqual(len(res), 1)

        cas = atc_obj.browse(cursor, uid, cas.id)
        self.assertEqual(cas.subtipus_id.name, "009")
        self.assertEqual(cas.resultat, "01")
        self.assertTrue(cas.tancar_cac_al_finalitzar_r1)
        self.assertEqual(cas.state, "done")
        r1_state = r1.read(["state"])[0]["state"]
        self.assertEqual(r1_state, "done")
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertFalse(pol.refacturacio_pendent)

    def crear_r1_i_cac_relacionats(self, txn, cursor, uid, context=None):
        if context is None:
            context = {}
        self.switch(txn, "comer")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        atc_obj = self.openerp.pool.get("giscedata.atc")
        wiz_o = self.openerp.pool.get("wizard.create.atc.from.polissa")
        pol_id = self.get_contract_id(txn, xml_id="polissa_0001")
        pol = pol_obj.browse(cursor, uid, pol_id)
        pol.distribuidora.write({"ref": 4444})
        # Creem un cas ATC
        wiz_cv = {"subtipus_id": 1}
        ctx = {"active_ids": [pol_id], "from_model": pol_obj._name}
        wiz_id = wiz_o.create(cursor, uid, wiz_cv, context=ctx)
        if context.get("atc_vals"):
            wiz_o.write(cursor, uid, [wiz_id], context.get("atc_vals"))
        ctx = {"active_ids": [pol_id], "from_model": pol_obj._name}
        wiz_o.create_atc_case(cursor, uid, [wiz_id], pol_obj._name, context=ctx)
        wiz = wiz_o.browse(cursor, uid, wiz_id)
        cas = atc_obj.browse(cursor, uid, wiz.generated_cases[0])
        pol = pol_obj.browse(cursor, uid, pol_id)
        self.assertEqual(cas.time_tracking_id.code, "0")

        # Cridem l'assistent de crear R1 desde ATC
        # Ha de tornar un diccionari que cridi el asistents de R1.
        # Ens quedarem amb el context i cridarem l'assistent amb aquest context
        wiz_o = self.openerp.pool.get("wizard.generate.r1.from.atc.case")
        ctx2 = {"active_ids": [cas.id], "from_model": pol_obj._name}
        wiz_id = wiz_o.create(cursor, uid, {}, context=ctx2)
        res = wiz_o.generate_r1(cursor, uid, [wiz_id], {"active_id": cas.id})
        context = eval(dict(res).get("context", "{}"))
        extra_values = context.get("extra_values")
        self.assertEqual(extra_values["auto_r1_atc"], True)
        self.assertEqual(context["polissa_id"], pol.id)
        self.assertEqual(extra_values["ref_id"], [cas.id])
        self.assertEqual(extra_values["ref_model"], "giscedata.atc")

        # Cridem l'assistent de crear R1 amb el context obringut.
        wiz_o = self.openerp.pool.get("wizard.subtype.r1")
        wiz_id = wiz_o.create(cursor, uid, {"comentaris": "TEST"}, context)
        res = wiz_o.action_create_r1_case(cursor, uid, [wiz_id], context)
        r1_id = dict(res).get("domain")[0][2]
        r1 = self.openerp.pool.get("giscedata.switching").browse(cursor, uid, r1_id)
        cac = cas.browse()[0]
        return cac, r1

    def test_import_r105_01_tancar_cac_al_finalitzar_r1(self):
        cursor = self.txn.cursor
        uid = self.txn.user
        sw_obj = self.openerp.pool.get("giscedata.switching")
        act_o = self.openerp.pool.get("giscedata.switching.activation.config")
        act_ids = act_o.search(cursor, uid, [], context={"active_test": False})
        act_o.write(cursor, uid, act_ids, {"active": True})

        cac, r1 = self.crear_r1_i_cac_relacionats(
            self.txn, cursor, uid, context={"atc_vals": {"tancar_cac_al_finalitzar_r1": True}}
        )
        self.assertEqual(cac.state, "pending")
        self.assertEqual(cac.time_tracking_id.code, "1")
        self.assertTrue(cac.tancar_cac_al_finalitzar_r1)

        r1.write({"codi_sollicitud": "201602231255"})
        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r102_new.xml"
        )
        with open(r1_xml_path, "r") as f:
            r102_xml = f.read()
            r102_xml = r102_xml.replace(
                "CodigoREEEmpresaEmisora>1234", "CodigoREEEmpresaEmisora>4444"
            )
        r1_xml_path = get_module_resource(
            "giscedata_switching", "tests", "fixtures", "r105_new.xml"
        )
        with open(r1_xml_path, "r") as f:
            r105_xml = f.read()
            r105_xml = r105_xml.replace(
                "CodigoREEEmpresaEmisora>1234", "CodigoREEEmpresaEmisora>4444"
            )

        # Al importar el R1-02 no hauria de passar res
        sw_obj.importar_xml(cursor, uid, r102_xml, "r102.xml")
        r1 = r1.browse()[0]
        cac = cac.browse()[0]
        self.assertEqual(r1.step_id.name, "02")
        self.assertEqual(r1.state, "open")
        self.assertEqual(cac.state, "pending")
        self.assertEqual(cac.time_tracking_id.code, "1")

        # Al importar el R1-05 s'ha de fer algunes accions al CAC
        sw_obj.importar_xml(cursor, uid, r105_xml, "r105_new.xml")
        r1 = r1.browse()[0]
        cac = cac.browse()[0]
        self.assertEqual(r1.step_id.name, "05")
        self.assertEqual(r1.state, "done")
        self.assertEqual(cac.state, "done")
        self.assertEqual(cac.time_tracking_id.code, "0")
        self.assertEqual(cac.agent_actual, "06")
        last_description = cac.history_line[0].description
        self.assertIn(u"Cas tancat automaticament al importar R1-05.", last_description)
        last_description = cac.history_line[1].description
        self.assertIn(u"R1-05 (seq. 01)", last_description)
        self.assertIn(u"Data Creació:", last_description)
        self.assertIn(u"Comentaris: Comentarios generales", last_description)
        self.assertIn(u"Documents: Sense documents adjunts", last_description)
        self.assertIn(u"Observacions: Observaciones generales", last_description)
