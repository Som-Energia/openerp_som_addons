# -*- coding: utf-8 -*-

from destral.transaction import Transaction
from giscedata_switching.tests.common_tests import TestSwitchingImport


class TestWizardReexportLog(TestSwitchingImport):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool
        self.wiz_o = self.pool.get("wizard.giscedata.switching.log.reexport")

    def tearDown(self):
        self.txn.stop()

    def test_wizard_reexport_files(self):
        self.switch(self.txn, "comer", other_id_name="res_partner_asus")
        uid = self.uid
        cursor = self.cursor
        contract_id = self.get_contract_id(self.txn)
        self.activar_polissa_CUPS(self.txn)
        step_id = self.create_case_and_step(cursor, uid, contract_id, "C1", "01")
        step_obj = self.openerp.pool.get("giscedata.switching.c1.01")
        sw_obj = self.openerp.pool.get("giscedata.switching")
        c101 = step_obj.browse(cursor, uid, step_id)
        c1 = sw_obj.browse(cursor, uid, c101.sw_id.id)
        log_obj = self.pool.get("giscedata.switching.log")
        sw_obj.exportar_xml(cursor, uid, c1.id)
        log_id = sorted(log_obj.search(cursor, uid, [("proces", "=", "C1")]))[
            -1
        ]
        log = log_obj.browse(cursor, uid, log_id)
        log_obj.write(cursor, uid, [log_id], {"status": "error"})
        wiz_reexport_id = self.wiz_o.create(cursor, uid, {}, context={"active_ids": [log.id]})

        self.wiz_o.reexport_files(
            cursor, uid, wiz_reexport_id, context={"active_ids": [log.id]}
        )

        wiz = self.wiz_o.browse(cursor, uid, wiz_reexport_id)
        self.assertEqual(wiz.state, "end")
        self.assertEqual(wiz.msg, "S'han processat 1 fitxers.\n")
