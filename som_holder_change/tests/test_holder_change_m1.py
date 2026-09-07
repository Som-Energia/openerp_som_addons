# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction


class TestHolderChangeM1(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.m1_obj = self.openerp.pool.get("som.holder.change.m1")
        self.polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.original_state = self.polissa_obj.read(
            self.cursor, self.uid, self.polissa_id, ["state"]
        )["state"]
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id, {"state": "activa"}
        )

    def tearDown(self):
        self.txn.stop()

    def test_execute_transfer_creates_one_m1_and_result_contract(self):
        owner_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_agrolait"
        )[1]

        result = self.m1_obj.execute(
            self.cursor,
            self.uid,
            self.polissa_id,
            "T",
            {"owner": owner_id, "pagador": owner_id},
        )

        self.assertNotEqual(result["result_polissa_id"], self.polissa_id)
        switching = self.openerp.pool.get("giscedata.switching").browse(
            self.cursor, self.uid, result["switching_id"]
        )
        self.assertEqual(switching.proces_id.name, "M1")
        self.assertEqual(switching.get_pas().sollicitudadm, "S")
        self.assertEqual(switching.get_pas().canvi_titular, "T")
        result_polissa = self.polissa_obj.browse(
            self.cursor, self.uid, result["result_polissa_id"]
        )
        self.assertEqual(result_polissa.titular.id, owner_id)
        report_backend = self.openerp.pool.get(
            "report.backend.condicions.particulars"
        )
        pas01 = report_backend.get_pas01(
            self.cursor,
            self.uid,
            self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id),
            {"m1_id": result["switching_id"]},
        )
        holder_data = report_backend.get_titular_data(
            self.cursor,
            self.uid,
            self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id),
            pas01,
        )
        self.assertEqual(holder_data["client_name"], result_polissa.titular.name)
        self.assertEqual(
            holder_data["client_vat"],
            result_polissa.titular.vat.replace("ES", ""),
        )
        self.assertEqual(holder_data["lang"], result_polissa.titular.lang)
        self.assertEqual(
            self.openerp.pool.get(
                "report.backend.condicions.particulars.m1"
            ).get_lang(
                self.cursor,
                self.uid,
                result["switching_id"],
            ),
            result_polissa.titular.lang,
        )

    def test_execute_subrogation_respects_same_contract_configuration(self):
        self.openerp.pool.get("res.config").set(
            self.cursor,
            self.uid,
            "sw_m1_owner_change_subrogacio_new_contract",
            "0",
        )
        owner_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_agrolait"
        )[1]

        result = self.m1_obj.execute(
            self.cursor,
            self.uid,
            self.polissa_id,
            "S",
            {"owner": owner_id, "pagador": owner_id},
        )

        self.assertEqual(result["result_polissa_id"], self.polissa_id)
        switching = self.openerp.pool.get("giscedata.switching").browse(
            self.cursor, self.uid, result["switching_id"]
        )
        self.assertEqual(switching.get_pas().canvi_titular, "S")
        self.assertEqual(
            switching.ref, "giscedata.polissa,{}".format(self.polissa_id)
        )

    def test_simulate_rolls_back_generated_m1_and_contract(self):
        owner_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "base", "res_partner_agrolait"
        )[1]
        switching_obj = self.openerp.pool.get("giscedata.switching")
        self.cursor.commit()
        switching_count = switching_obj.search_count(
            self.cursor, self.uid, []
        )
        contract_count = self.polissa_obj.search_count(
            self.cursor, self.uid, []
        )

        try:
            result = self.m1_obj.simulate(
                self.cursor,
                self.uid,
                self.polissa_id,
                "T",
                {"owner": owner_id, "pagador": owner_id},
            )

            self.assertEqual(result, {"valid": True})
            self.assertEqual(
                switching_obj.search_count(self.cursor, self.uid, []),
                switching_count,
            )
            self.assertEqual(
                self.polissa_obj.search_count(self.cursor, self.uid, []),
                contract_count,
            )
        finally:
            self.polissa_obj.write(
                self.cursor,
                self.uid,
                self.polissa_id,
                {"state": self.original_state},
            )
            self.cursor.commit()
