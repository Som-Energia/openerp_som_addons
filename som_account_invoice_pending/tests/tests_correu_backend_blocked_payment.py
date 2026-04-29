# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestCorreuBackendBlockedPayment(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_fue_bo_social(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        # Get a test invoice with pending state
        fact_id = fact_obj.search(cursor, uid, [], limit=1)[0]
        fact = fact_obj.browse(cursor, uid, fact_id)
        pol_id = fact.polissa_id.id

        # Get fue_bo_social_pending_state ID
        fue_bs_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_bo_social_pending_state"
        )[1]

        # Set cobrament_bloquejat to True and pending_state to fue_bo_social
        pol_obj.write(cursor, uid, pol_id, {"cobrament_bloquejat": True})
        fact_obj.write(cursor, uid, fact_id, {"pending_state": fue_bs_id})

        # Instantiate backend and call get_factura
        backend = backend_obj
        result = backend.get_factura(cursor, uid, fact, context={})

        self.assertTrue(result.get("hasBlockedPayment"))

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_fue_default(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fact_id = fact_obj.search(cursor, uid, [], limit=1)[0]
        fact = fact_obj.browse(cursor, uid, fact_id)
        pol_id = fact.polissa_id.id

        fue_df_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_default_pending_state"
        )[1]

        pol_obj.write(cursor, uid, pol_id, {"cobrament_bloquejat": True})
        fact_obj.write(cursor, uid, fact_id, {"pending_state": fue_df_id})

        backend = backend_obj
        result = backend.get_factura(cursor, uid, fact, context={})

        self.assertTrue(result.get("hasBlockedPayment"))

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_reclamacio_en_curs(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fact_id = fact_obj.search(cursor, uid, [], limit=1)[0]
        fact = fact_obj.browse(cursor, uid, fact_id)
        pol_id = fact.polissa_id.id

        r1_bs_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "reclamacio_en_curs_pending_state"
        )[1]

        pol_obj.write(cursor, uid, pol_id, {"cobrament_bloquejat": True})
        fact_obj.write(cursor, uid, fact_id, {"pending_state": r1_bs_id})

        backend = backend_obj
        result = backend.get_factura(cursor, uid, fact, context={})

        self.assertTrue(result.get("hasBlockedPayment"))

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_default_reclamacio_en_curs(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fact_id = fact_obj.search(cursor, uid, [], limit=1)[0]
        fact = fact_obj.browse(cursor, uid, fact_id)
        pol_id = fact.polissa_id.id

        r1_df_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "default_reclamacio_en_curs_pending_state"
        )[1]

        pol_obj.write(cursor, uid, pol_id, {"cobrament_bloquejat": True})
        fact_obj.write(cursor, uid, fact_id, {"pending_state": r1_df_id})

        backend = backend_obj
        result = backend.get_factura(cursor, uid, fact, context={})

        self.assertTrue(result.get("hasBlockedPayment"))

    def test_hasBlockedPayment_false_when_cobrament_bloquejat_false(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fact_id = fact_obj.search(cursor, uid, [], limit=1)[0]
        fact = fact_obj.browse(cursor, uid, fact_id)
        pol_id = fact.polissa_id.id

        fue_bs_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_bo_social_pending_state"
        )[1]

        # Set cobrament_bloquejat to False (default)
        pol_obj.write(cursor, uid, pol_id, {"cobrament_bloquejat": False})
        fact_obj.write(cursor, uid, fact_id, {"pending_state": fue_bs_id})

        backend = backend_obj
        result = backend.get_factura(cursor, uid, fact, context={})

        self.assertFalse(result.get("hasBlockedPayment"))

    def test_hasBlockedPayment_false_when_no_pending_state(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fact_id = fact_obj.search(cursor, uid, [], limit=1)[0]
        fact = fact_obj.browse(cursor, uid, fact_id)
        pol_id = fact.polissa_id.id

        # Set cobrament_bloquejat but no pending_state
        pol_obj.write(cursor, uid, pol_id, {"cobrament_bloquejat": True})
        fact_obj.write(cursor, uid, fact_id, {"pending_state": False})

        backend = backend_obj
        result = backend.get_factura(cursor, uid, fact, context={})

        self.assertFalse(result.get("hasBlockedPayment"))

    def test_hasBlockedPayment_false_when_pending_state_not_blocked(self):
        cursor = self.cursor
        uid = self.uid

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fact_id = fact_obj.search(cursor, uid, [], limit=1)[0]
        fact = fact_obj.browse(cursor, uid, fact_id)
        pol_id = fact.polissa_id.id

        # Create a new pending state (not one of the blocked ones)
        pending_obj = self.pool.get("account.invoice.pending.state")
        pending_id = pending_obj.create(cursor, uid, {
            "name": "Test Pending State",
            "code": "test_pending"
        })

        pol_obj.write(cursor, uid, pol_id, {"cobrament_bloquejat": True})
        fact_obj.write(cursor, uid, fact_id, {"pending_state": pending_id})

        backend = backend_obj
        result = backend.get_factura(cursor, uid, fact, context={})

        self.assertFalse(result.get("hasBlockedPayment"))

        # Cleanup
        pending_obj.unlink(cursor, uid, [pending_id])
