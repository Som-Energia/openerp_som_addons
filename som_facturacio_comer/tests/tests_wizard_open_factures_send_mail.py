# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestOpenFacturesSendMail(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test_wizard_open_factures_send_mail_one_fact(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.open.factures.send.mail")
        imd_obj = self.pool.get("ir.model.data")
        clot_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "cont_lot_0001"
        )[1]
        clot = clot_obj.browse(cursor, uid, clot_id)
        pol_id = clot.polissa_id.id
        fact_id = fact_obj.search(
            cursor,
            uid,
            [("polissa_id", "=", pol_id), ("type", "=", "out_invoice"), ("state", "=", "draft")],
            limit=1,
        )[0]
        fact_obj.write(cursor, uid, fact_id, {"lot_facturacio": clot.lot_id.id})
        clot_obj.write(
            cursor, uid, clot_id, {"state": "facturat_incident", "incidence_checked": False}
        )
        context = {"active_ids": [clot_id], "active_id": clot_id}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        res = wiz_obj.open_factures_send_mail(cursor, uid, wiz_id, context=context)

        clot = clot_obj.browse(cursor, uid, clot_id)
        fact = fact_obj.browse(cursor, uid, fact_id)
        self.assertEqual(clot.state, "finalitzat")
        self.assertEqual(fact.state, "open")
        self.assertTrue("'src_rec_id': {}".format(fact_id) in res["context"])
        self.assertTrue("'src_rec_ids': {}".format([fact_id]) in res["context"])

    def test_wizard_open_factures_send_mail_many_fact(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.open.factures.send.mail")
        imd_obj = self.pool.get("ir.model.data")
        clot_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "cont_lot_0001"
        )[1]
        clot = clot_obj.browse(cursor, uid, clot_id)
        pol_id = clot.polissa_id.id
        fact_ids = fact_obj.search(
            cursor,
            uid,
            [("polissa_id", "=", pol_id), ("type", "=", "out_invoice"), ("state", "=", "draft")],
            limit=2,
        )
        self.assertEqual(len(fact_ids), 2)
        fact_obj.write(cursor, uid, fact_ids, {"lot_facturacio": clot.lot_id.id})
        clot_obj.write(
            cursor, uid, clot_id, {"state": "facturat_incident", "incidence_checked": False}
        )
        context = {"active_ids": [clot_id], "active_id": clot_id}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        res = wiz_obj.open_factures_send_mail(cursor, uid, wiz_id, context=context)

        clot = clot_obj.browse(cursor, uid, clot_id)
        facts = fact_obj.browse(cursor, uid, fact_ids)
        self.assertEqual(clot.state, "finalitzat")
        self.assertEqual([fact.state for fact in facts], ["open", "open"])
        self.assertTrue("'src_rec_id': {}".format(fact_ids[0]) in res["context"])
        self.assertTrue("'src_rec_ids': {}".format(fact_ids) in res["context"])

    def test_wizard_open_factures_send_mail_zero_fact(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.open.factures.send.mail")
        imd_obj = self.pool.get("ir.model.data")
        clot_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "cont_lot_0001"
        )[1]
        clot = clot_obj.browse(cursor, uid, clot_id)
        pol_id = clot.polissa_id.id
        fact_id = fact_obj.search(
            cursor,
            uid,
            [
                ("polissa_id", "=", pol_id),
                ("type", "=", "out_invoice"),
                ("state", "=", "draft"),
                ("lot_facturacio", "=", clot.lot_id.id),
            ],
        )
        self.assertFalse(fact_id)
        clot_obj.write(cursor, uid, clot_id, {"state": "facturat"})
        context = {"active_ids": [clot_id], "active_id": clot_id}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        with self.assertRaises(Exception) as e:
            wiz_obj.open_factures_send_mail(cursor, uid, wiz_id, context=context)

        self.assertEqual(
            e.exception.message, "warning -- Error!\n\nNo s'ha pogut obrir cap factura!"
        )
        clot = clot_obj.browse(cursor, uid, clot_id)
        self.assertEqual(clot.state, "facturat")

    def test_wizard_open_factures_send_mail_facturat(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.open.factures.send.mail")
        imd_obj = self.pool.get("ir.model.data")
        clot_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "cont_lot_0001"
        )[1]
        clot = clot_obj.browse(cursor, uid, clot_id)
        pol_id = clot.polissa_id.id
        fact_id = fact_obj.search(
            cursor,
            uid,
            [("polissa_id", "=", pol_id), ("type", "=", "out_invoice"), ("state", "=", "draft")],
            limit=1,
        )[0]
        fact_obj.write(cursor, uid, fact_id, {"lot_facturacio": clot.lot_id.id})
        clot_obj.write(cursor, uid, clot_id, {"state": "facturat"})
        context = {"active_ids": [clot_id], "active_id": clot_id}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        res = wiz_obj.open_factures_send_mail(cursor, uid, wiz_id, context=context)

        clot = clot_obj.browse(cursor, uid, clot_id)
        fact = fact_obj.browse(cursor, uid, fact_id)
        self.assertEqual(clot.state, "finalitzat")
        self.assertEqual(fact.state, "open")
        self.assertTrue("'src_rec_id': {}".format(fact_id) in res["context"])
        self.assertTrue("'src_rec_ids': {}".format([fact_id]) in res["context"])

    def test_wizard_open_factures_send_mail_many_clots(self):
        cursor = self.cursor
        uid = self.uid

        clot_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        wiz_obj = self.pool.get("wizard.open.factures.send.mail")
        imd_obj = self.pool.get("ir.model.data")
        clot_id1 = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "cont_lot_0001"
        )[1]
        clot_id2 = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "cont_lot_0002"
        )[1]
        clots = clot_obj.browse(cursor, uid, [clot_id1, clot_id2])
        pol_id1 = clots[0].polissa_id.id
        pol_id2 = clots[1].polissa_id.id
        fact_id1 = fact_obj.search(
            cursor,
            uid,
            [("polissa_id", "=", pol_id1), ("type", "=", "out_invoice"), ("state", "=", "draft")],
            limit=1,
        )[0]
        fact_id2 = fact_obj.search(
            cursor,
            uid,
            [("polissa_id", "!=", pol_id1), ("type", "=", "out_invoice"), ("state", "=", "draft")],
            limit=1,
        )[0]
        fact_obj.write(cursor, uid, fact_id1, {"lot_facturacio": clots[0].lot_id.id})
        fact_obj.write(
            cursor, uid, fact_id2, {"lot_facturacio": clots[1].lot_id.id, "polissa_id": pol_id2}
        )
        clot_obj.write(
            cursor,
            uid,
            [clot_id1, clot_id2],
            {"state": "facturat_incident", "incidence_checked": False},
        )
        context = {"active_ids": [clot_id1, clot_id2], "active_id": clot_id1}
        wiz_id = wiz_obj.create(cursor, uid, {}, context=context)
        res = wiz_obj.open_factures_send_mail(cursor, uid, wiz_id, context=context)

        clot1 = clot_obj.browse(cursor, uid, clot_id1)
        clot2 = clot_obj.browse(cursor, uid, clot_id2)

        facts = fact_obj.browse(cursor, uid, [fact_id1, fact_id2])
        self.assertEqual(clot1.state, "finalitzat")
        self.assertEqual(clot2.state, "finalitzat")

        self.assertEqual([fact.state for fact in facts], ["open", "open"])
        self.assertTrue("'src_rec_id': {}".format(fact_id1) in res["context"])
        self.assertTrue("'src_rec_ids': {}".format([fact_id1, fact_id2]) in res["context"])
