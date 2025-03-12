# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv.osv import except_osv
from destral.transaction import Transaction
import mock
from giscedata_switching.tests.common_tests import TestSwitchingImport
import unittest

from .. import wizard


class TestWizardValidateD101(TestSwitchingImport):
    def create_d1_case_at_step_01(self, txn):
        self.switch(txn, "distri")
        uid = txn.user
        cursor = txn.cursor

        contract_id = self.get_contract_id(txn)

        imd_obj = self.openerp.pool.get("ir.model.data")
        tarifa_id = imd_obj.get_object_reference(cursor, uid, "giscedata_polissa", "tarifa_20TD")[1]
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        pol_obj.write(cursor, uid, [contract_id], {"tarifa": tarifa_id})

        self.change_polissa_comer(txn)
        self.update_polissa_distri(txn)
        self.activar_polissa_CUPS(txn)
        context = {
            "contract_id": contract_id,
            "contract_ids": [contract_id],
        }
        d101_id = self.create_case_and_step(
            cursor, uid, contract_id, "D1", "01", {"whereiam": "distri"}
        )

        d101_obj = self.openerp.pool.get("giscedata.switching.d1.01")
        d101 = d101_obj.browse(cursor, uid, d101_id)
        d1_id = d101.sw_id.id

        autoconsum_id = self.crear_autoconsum(txn)

        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        # cups_obj = self.openerp.pool.get("giscedata.cups.ps")

        cups_id = polissa_obj.read(cursor, uid, contract_id, ["cups"])["cups"]
        self.activar_autoconsum_a_cups(txn, autoconsum_id, cups_id[0])
        # cups_obj.write(cursor, uid, cups_id[0], {"autoconsum_id": autoconsum_id})

        # Button create case
        context.update({"autoconsum_id": autoconsum_id})

        sw_obj = self.openerp.pool.get("giscedata.switching")
        self.switch(txn, "comer")

        cups_id = sw_obj.read(cursor, uid, d1_id, ["cups_id"])["cups_id"]
        sw_obj.write(cursor, uid, d1_id, {"cups_id": cups_id[0]})
        return d1_id

    def test__create_step_d1_02_autoconsum__reject(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            sw_obj = self.openerp.pool.get("giscedata.switching")
            d102_obj = self.openerp.pool.get("giscedata.switching.d1.02")
            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")

            d1_id = self.create_d1_case_at_step_01(txn)

            rejection_comment = u"This is an example of a rejection comment"
            wiz_init = {"sw_id": d1_id}
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)
            d102_id = wiz._create_step_d1_02_autoconsum(
                sw_id=d1_id, is_rejected=True, rejection_comment=rejection_comment, set_pending=True
            )

            motiu_obj = self.openerp.pool.get("giscedata.switching.motiu.rebuig")
            motiu_rebuig_id = motiu_obj.search(cursor, uid, [("name", "=", "F1")])
            motiu_rebuig_text = motiu_obj.read(cursor, uid, motiu_rebuig_id[0], ["text"])["text"]

            rejection_description = motiu_rebuig_text + ": {}".format(rejection_comment)

            d1 = sw_obj.browse(cursor, uid, d1_id)
            d102 = d102_obj.browse(cursor, uid, d102_id)

            self.assertEqual(d102.sw_id.id, d1_id)
            self.assertTrue(d102.rebuig)
            self.assertTrue(d1.validacio_pendent)
            self.assertTrue(d102.validacio_pendent)
            self.assertEqual(d102.rebuig_ids[-1].desc_rebuig, rejection_description)

            self.assertEqual(d102.motiu_rebuig, rejection_description)

            self.assertEqual(
                d102.sw_id.history_line[0].description.split(":")[-1].strip(), rejection_comment
            )

    def test__create_step_d1_02_autoconsum__accept(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            sw_obj = self.openerp.pool.get("giscedata.switching")
            d102_obj = self.openerp.pool.get("giscedata.switching.d1.02")
            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")

            d1_id = self.create_d1_case_at_step_01(txn)

            wiz_init = {"sw_id": d1_id}
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)

            d102_id = wiz._create_step_d1_02_autoconsum(d1_id, is_rejected=False, set_pending=True)

            d1 = sw_obj.browse(cursor, uid, d1_id)
            d102 = d102_obj.browse(cursor, uid, d102_id)

            self.assertEqual(d102.sw_id.id, d1_id)
            self.assertFalse(d102.rebuig)
            self.assertFalse(d1.validacio_pendent)
            self.assertFalse(d102.validacio_pendent)

            expected_history_msg = u"D1-01 Acceptat des de l'assistent de validació de D1-01"
            self.assertEqual(
                d102.sw_id.history_line[0].description.split(":")[-1].strip(), expected_history_msg
            )

    def test__create_case_m1_01_autoconsum_no_auto(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            sw_obj = self.openerp.pool.get("giscedata.switching")
            wiz_step_obj = self.openerp.pool.get("wizard.create.step")

            pol_id = self.get_contract_id(txn)

            # create d101
            d1_id = self.create_d1_case_at_step_01(txn)

            # create d102 using previous existing wiz
            params = {
                "step": "02",
                "option": "A",
                "step_is_rejectable": True,
                "check_repeated": True,
            }
            wiz_step_id = wiz_step_obj.create(cursor, uid, params, context={"active_ids": [d1_id]})
            wiz_step = wiz_step_obj.browse(cursor, uid, wiz_step_id)
            wiz_step.action_create_steps(context={"active_ids": [d1_id]})
            wiz_step = wiz_step.browse()[0]
            sw_obj.write(cursor, uid, [d1_id], {"additional_info": "Autoconsum"})

            # wizard to test
            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")

            wiz_init = {"sw_id": d1_id}
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)
            with self.assertRaises(except_osv) as error:
                wiz._create_case_m1_01_autoconsum(pol_id)
            self.assertIn(
                u"No s'ha pogut crear el cas M1 per la pòlissa 1 al no haver-hi un autoconsum",
                error.exception.message,
            )

    def test__create_case_m1_01_autoconsum__exception(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            self.openerp.pool.get("giscedata.switching")
            self.openerp.pool.get("giscedata.switching.m1.01")
            self.openerp.pool.get("wizard.create.step")
            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")

            pol_id = self.get_contract_id(txn)

            # create d101
            d1_id = self.create_d1_case_at_step_01(txn)

            wiz_init = {"sw_id": d1_id}
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz_validate_obj.browse(cursor, uid, wiz_id)

            with self.assertRaises(except_osv) as error:
                wiz_validate_obj._create_case_m1_01_autoconsum(cursor, uid, wiz_id, pol_id)

            self.assertIn(
                u"Alerta, la modalitat d'autoconsum no ha estat acceptada pel client, vols seguir?",
                error.exception.message,
            )

    def test__validate_d101__reject(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            self.openerp.pool.get("giscedata.switching")
            d102_obj = self.openerp.pool.get("giscedata.switching.d1.02")
            d1_id = self.create_d1_case_at_step_01(txn)

            rejection_comment = u"This is an example of a rejection comment"

            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")

            wiz_init = {
                "sw_id": d1_id,
                "is_rejected": True,
                "rejection_comment": rejection_comment,
                "set_pending": True,
            }
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)
            wiz.validate_d101_autoconsum()

            d102_id = wiz.read(["generated_d102"])[0]["generated_d102"]
            m1_id = wiz.read(["generated_m1"])[0]["generated_m1"]

            motiu_obj = self.openerp.pool.get("giscedata.switching.motiu.rebuig")
            motiu_rebuig_id = motiu_obj.search(cursor, uid, [("name", "=", "F1")])
            motiu_rebuig_text = motiu_obj.read(cursor, uid, motiu_rebuig_id[0], ["text"])["text"]

            rejection_description = motiu_rebuig_text + ": {}".format(rejection_comment)

            d102 = d102_obj.browse(cursor, uid, d102_id)

            self.assertEqual(d102.sw_id.id, d1_id)
            self.assertTrue(d102.rebuig)
            self.assertEqual(d102.rebuig_ids[-1].desc_rebuig, rejection_description)

            self.assertEqual(d102.motiu_rebuig, rejection_description)
            self.assertFalse(m1_id)

    @mock.patch.object(
        wizard.wizard_validate_d101.GiscedataSwitchingWizardValidateD101,
        "_create_case_m1_01_autoconsum",
    )
    def test__validate_d101__accept_m101_exception(self, mock_create_case_m1_01):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            mock_create_case_m1_01.side_effect = except_osv(cursor, uid)

            sw_obj = self.openerp.pool.get("giscedata.switching")
            d102_obj = self.openerp.pool.get("giscedata.switching.d1.02")
            self.openerp.pool.get("giscedata.switching.m1.01")
            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")

            d1_id = self.create_d1_case_at_step_01(txn)

            wiz_init = {"sw_id": d1_id}
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)
            with self.assertRaises(except_osv):
                wiz.validate_d101_autoconsum()

            d1 = sw_obj.browse(cursor, uid, d1_id)
            step_info = d1.step_ids[-1]
            d102_id = int(step_info.pas_id.split(",")[-1])
            d102 = d102_obj.browse(cursor, uid, d102_id)

            self.assertTrue(d1.validacio_pendent)

            historize_msg = (
                "Hi ha hagut un error al generar el cas M1 després d'acceptar "
                + "el D1-01 mitjançant l'assistent de validació"
            )
            self.assertEqual(
                d102.sw_id.history_line[0].description.split(":")[0].strip(), historize_msg
            )

    def test__create_step_d1_02_motiu_06__accept_done(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            sw_obj = self.openerp.pool.get("giscedata.switching")
            d101_obj = self.openerp.pool.get("giscedata.switching.d1.01")
            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")
            gen_obj = self.openerp.pool.get("giscedata.autoconsum.generador")

            d1_id = self.create_d1_case_at_step_01(txn)

            sw = sw_obj.browse(cursor, uid, d1_id)
            pas_id = sw.step_ids[0].pas_id
            id_pas = int(pas_id.split(",")[1])
            d101_obj.write(cursor, uid, [id_pas], {"motiu_canvi": "06"})

            imd_obj = self.openerp.pool.get("ir.model.data")
            auto_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_cups", "autoconsum_collectiu_xarxa_interior")[1]

            gen_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_cups", "generador_autoconsum_collectiu_xarxa_interior")[1]

            gen_obj.write(cursor, uid, gen_id, {"partner_id": 3})

            pol_obj = self.openerp.pool.get("giscedata.polissa")

            tipus_subseccio = pol_obj.read(
                cursor, uid, sw.cups_polissa_id.id, ["tipus_subseccio"])["tipus_subseccio"]
            self.assertEqual(tipus_subseccio, '00')

            wiz_init = {"sw_id": d1_id, 'autoconsum_id': auto_id}
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)

            d102, m101 = wiz.validate_d101_autoconsum()

            tipus_subseccio = pol_obj.read(
                cursor, uid, sw.cups_polissa_id.id, ["tipus_subseccio"])["tipus_subseccio"]
            self.assertEqual(tipus_subseccio, '00')

            # m1 esborrany
            self.assertNotEqual(m101, False)
            self.assertEqual(d102, False)

    @unittest.skip("Waiting for ATR3.0")
    def test__create_case_m1_01_motiu_06__S_R(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor

            m101_obj = self.openerp.pool.get("giscedata.switching.m1.01")

            pol_id = self.get_contract_id(txn)

            # wizard to test
            sw_obj = self.openerp.pool.get("giscedata.switching")
            d101_obj = self.openerp.pool.get("giscedata.switching.d1.01")
            self.openerp.pool.get("giscedata.switching.d1.02")
            wiz_validate_obj = self.openerp.pool.get("wizard.validate.d101")

            d1_id = self.create_d1_case_at_step_01(txn)

            sw = sw_obj.browse(cursor, uid, d1_id)
            pas_id = sw.step_ids[0].pas_id
            id_pas = int(pas_id.split(",")[1])
            d101_obj.write(cursor, uid, [id_pas], {"motiu_canvi": "06"})

            wiz_init = {"sw_id": d1_id}
            wiz_id = wiz_validate_obj.create(cursor, uid, wiz_init)
            wiz = wiz_validate_obj.browse(cursor, uid, wiz_id)

            wiz.validate_d101_autoconsum()

            m1_id = wiz.read(["generated_m1"])[0]["generated_m1"]

            m1 = sw_obj.browse(cursor, uid, m1_id)

            self.assertEqual(m1.state, "draft")
            self.assertEqual(len(m1.step_ids), 1)
            self.assertEqual(m1.polissa_ref_id.id, pol_id)
            self.assertEqual(
                m1.additional_info[0:48], "(S)[R] Mod. Acord repartiment/fitxer coeficients"
            )
            id_pas = int(m1.step_ids[0].pas_id.split(",")[1])
            pas = m101_obj.browse(cursor, uid, id_pas)
            self.assertEqual(pas.sollicitudadm, "S")
            self.assertEqual(pas.canvi_titular, "R")
