# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction


class TestsWzardSwitchingB1(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def tests__wizardSwitchingB1__without_phone_number(self):
        """
        Test wizard without phone number, case ATR B1 is created phone number equal to partner phone number
        """
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("giscedata.switching.b101.wizard")

        pol_id = imd_obj.get_object_reference(cursor, uid, "giscedata_polissa", "polissa_0001")[1]

        pol_obj = self.pool.get("giscedata.polissa")
        pol_obj.write(
            cursor,
            uid,
            pol_id,
            {
                "state": "activa",
            },
        )
        polissa = pol_obj.browse(cursor, uid, pol_id)
        partner_obj = self.pool.get("res.partner")
        partner_obj.write(cursor, uid, polissa.distribuidora.id, {"ref": "01"})
        partner_obj.write(cursor, uid, 1, {"ref": "01"})

        ctx = {"contract_id": pol_id, "from_model": "giscedata.polissa"}
        wiz_cv = {"motive": "01"}
        wiz_id = wiz_o.create(cursor, uid, wiz_cv, context=ctx)

        wiz_o.genera_casos_atr(cursor, uid, [wiz_id], context=ctx)
        wiz = wiz_o.browse(cursor, uid, wiz_id)

        cas_generat_id = int(wiz["casos_generats"][1:-1])

        cas_obj = self.pool.get("giscedata.switching.b1.01")
        cas_ids = cas_obj.search(cursor, uid, [("sw_id", "=", cas_generat_id)])

        if len(cas_ids) > 0:
            cas_b101 = cas_obj.browse(cursor, uid, cas_ids[0])

            direccio = pol_obj.get_address_with_phone(cursor, uid, pol_id)

            self.assertEqual(cas_b101.cont_telefons[0].numero, direccio.phone)

    def tests__wizardSwitchingB1__with_phone_number(self):
        """
        Test wizard with phone number, case ATR B1 is created with phone number
        """
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.pool.get("ir.model.data")
        wiz_o = self.pool.get("giscedata.switching.b101.wizard")

        pol_id = imd_obj.get_object_reference(cursor, uid, "giscedata_polissa", "polissa_0001")[1]

        pol_obj = self.pool.get("giscedata.polissa")
        pol_obj.write(
            cursor,
            uid,
            pol_id,
            {
                "state": "activa",
            },
        )
        polissa = pol_obj.browse(cursor, uid, pol_id)
        partner_obj = self.pool.get("res.partner")
        partner_obj.write(cursor, uid, polissa.distribuidora.id, {"ref": "01"})
        partner_obj.write(cursor, uid, 1, {"ref": "01"})

        ctx = {"contract_id": pol_id, "from_model": "giscedata.polissa"}
        wiz_cv = {"motive": "01", "phone_num": "972123456"}
        wiz_id = wiz_o.create(cursor, uid, wiz_cv, context=ctx)

        wiz_o.genera_casos_atr(cursor, uid, [wiz_id], context=ctx)
        wiz = wiz_o.browse(cursor, uid, wiz_id)

        cas_generat_id = int(wiz["casos_generats"][1:-1])

        cas_obj = self.pool.get("giscedata.switching.b1.01")
        cas_ids = cas_obj.search(cursor, uid, [("sw_id", "=", cas_generat_id)])

        if len(cas_ids) > 0:
            cas_b101 = cas_obj.browse(cursor, uid, cas_ids[0])

            self.assertEqual(cas_b101.cont_telefons[0].numero, "972123456")
