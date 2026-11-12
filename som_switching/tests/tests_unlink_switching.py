# -*- coding: utf-8 -*-

from destral.transaction import Transaction
from giscedata_switching.tests.common_tests import TestSwitchingImport


class TestUnlinkSwitching(TestSwitchingImport):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test_switching_and_atc_is_cancelled_on_unlink(self):
        """
        Test per comprovar que l'unlink no elimina sino que cancela el ATR
        """
        sw_obj = self.pool.get("giscedata.switching")
        atc_obj = self.pool.get("giscedata.atc")
        step_obj = self.openerp.pool.get("giscedata.switching.r1.01")
        imd_obj = self.openerp.pool.get("ir.model.data")

        atc_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "cas_atc_0001"
        )[1]

        # it needs enviament pendent
        self.switch(self.txn, "comer")
        contract_id = self.get_contract_id(self.txn)

        step_id = self.create_case_and_step(self.cursor, self.uid, contract_id, "R1", "01")
        r101 = step_obj.browse(self.cursor, self.uid, step_id)
        r101.write({"enviament_pendent": True})

        sw = sw_obj.browse(self.cursor, self.uid, r101.sw_id.id)
        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        sw_obj.write(
            self.cursor, self.uid, sw.id, {"ref": "giscedata.atc," + str(atc_id)}
        )

        sw.unlink()

        self.assertEqual(sw.state, "cancel")
        self.assertEqual(atc.state, "cancel")

    def test_switching_in_progress_cant_be_cancelled(self):
        """
        Test per comprovar que si esta en progres no es pot cancel·lar
        """
        sw_obj = self.pool.get("giscedata.switching")
        imd_obj = self.openerp.pool.get("ir.model.data")

        sw_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_switching", "sw_001"
        )[1]
        sw = sw_obj.browse(self.cursor, self.uid, sw_id)

        sw_obj.write(self.cursor, self.uid, sw_id, {"state": "pending"})

        try:
            sw_obj.case_cancel(self.cursor, self.uid, sw_id)
        except Exception as e:
            sw_err = e

        self.assertEqual(
            sw_err.value,
            "No es poden cancel·lar casos ATR en marxa, revisa els protocols o demana ajuda."
        )

        self.assertEqual(sw.state, "pending")
