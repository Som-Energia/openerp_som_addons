# -*- coding: utf-8 -*-
from datetime import datetime
from destral import testing
from destral.transaction import Transaction


class TestWizardDefinirInformacioAddicional(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def get_factura_id(self):
        imd_obj = self.pool.get("ir.model.data")
        return imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0001"
        )[1]

    def test_afegeix_comment_amb_data_a_factura_sense_comment(self):
        cursor = self.cursor
        uid = self.uid
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.definir.informacio.addicional")

        fact_id = self.get_factura_id()
        fact_obj.write(cursor, uid, fact_id, {"comment": False})

        context = {"active_ids": [fact_id], "active_id": fact_id}
        wiz_id = wiz_obj.create(cursor, uid, {"comment": "Text nou"}, context=context)
        wiz_obj.definir_informacio_addicional(cursor, uid, [wiz_id], context=context)

        fact = fact_obj.browse(cursor, uid, fact_id)
        today = datetime.today().strftime('%d/%m/%Y')
        expected = "{}: Text nou".format(today)
        self.assertEqual(fact.comment, expected)

    def test_afegeix_comment_amb_data_a_factura_amb_comment_existent(self):
        cursor = self.cursor
        uid = self.uid
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.definir.informacio.addicional")

        fact_id = self.get_factura_id()
        fact_obj.write(cursor, uid, fact_id, {"comment": "Comment existent"})

        context = {"active_ids": [fact_id], "active_id": fact_id}
        wiz_id = wiz_obj.create(cursor, uid, {"comment": "Text nou"}, context=context)
        wiz_obj.definir_informacio_addicional(cursor, uid, [wiz_id], context=context)

        fact = fact_obj.browse(cursor, uid, fact_id)
        today = datetime.today().strftime('%d/%m/%Y')
        expected = "{}: Text nou\nComment existent".format(today)
        self.assertEqual(fact.comment, expected)

    def test_wizard_comment_buit_no_sobreescriu(self):
        cursor = self.cursor
        uid = self.uid
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.definir.informacio.addicional")

        fact_id = self.get_factura_id()
        fact_obj.write(cursor, uid, fact_id, {"comment": "Comment existent"})

        context = {"active_ids": [fact_id], "active_id": fact_id}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        wiz_obj.definir_informacio_addicional(cursor, uid, [wiz_id], context=context)

        fact = fact_obj.browse(cursor, uid, fact_id)
        self.assertFalse(fact.comment)

    def test_multiples_factures(self):
        cursor = self.cursor
        uid = self.uid
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.definir.informacio.addicional")
        imd_obj = self.pool.get("ir.model.data")

        fact_id1 = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]
        fact_id2 = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0002"
        )[1]

        fact_obj.write(cursor, uid, fact_id1, {"comment": "Comment existent"})
        fact_obj.write(cursor, uid, fact_id2, {"comment": False})

        context = {"active_ids": [fact_id1, fact_id2], "active_id": fact_id1}
        wiz_id = wiz_obj.create(cursor, uid, {"comment": "Text nou"}, context=context)
        wiz_obj.definir_informacio_addicional(cursor, uid, [wiz_id], context=context)

        today = datetime.today().strftime('%d/%m/%Y')

        fact1 = fact_obj.browse(cursor, uid, fact_id1)
        expected1 = "{}: Text nou\nComment existent".format(today)
        self.assertEqual(fact1.comment, expected1)

        fact2 = fact_obj.browse(cursor, uid, fact_id2)
        expected2 = "{}: Text nou".format(today)
        self.assertEqual(fact2.comment, expected2)

    def test_wizard_state_end(self):
        cursor = self.cursor
        uid = self.uid
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.definir.informacio.addicional")

        fact_id = self.get_factura_id()
        fact_obj.write(cursor, uid, fact_id, {"comment": False})

        context = {"active_ids": [fact_id], "active_id": fact_id}
        wiz_id = wiz_obj.create(cursor, uid, {"comment": "Text nou"}, context=context)
        wiz_obj.definir_informacio_addicional(cursor, uid, [wiz_id], context=context)

        wiz = wiz_obj.read(cursor, uid, wiz_id, ["state"])
        self.assertEqual(wiz["state"], "end")
