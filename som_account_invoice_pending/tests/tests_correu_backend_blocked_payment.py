# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import mock


class TestCorreuBackendBlockedPayment(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def _create_mock_pol(self, cobrament_bloquejat):
        """Create a mock polissa object."""
        mock_pol = mock.MagicMock()
        mock_pol.cobrament_bloquejat = cobrament_bloquejat
        return mock_pol

    def _create_mock_fact(self, pending_state_id):
        """Create a mock factura object."""
        mock_fact = mock.MagicMock()
        if pending_state_id:
            mock_pending = mock.MagicMock()
            mock_pending.id = pending_state_id
            mock_fact.pending_state = mock_pending
        else:
            mock_fact.pending_state = None
        return mock_fact

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_fue_bo_social(self):
        """Test blocked payment returns True when cobrament_bloquejat + fue_bo_social."""
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fue_bs_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_bo_social_pending_state"
        )[1]

        pol = self._create_mock_pol(cobrament_bloquejat=True)
        fact = self._create_mock_fact(pending_state_id=fue_bs_id)

        result = backend_obj._invoice_has_blocked_payment(cursor, uid, pol, fact)

        self.assertTrue(result)

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_fue_default(self):
        """Test blocked payment returns True when cobrament_bloquejat + fue_default."""
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fue_df_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_default_pending_state"
        )[1]

        pol = self._create_mock_pol(cobrament_bloquejat=True)
        fact = self._create_mock_fact(pending_state_id=fue_df_id)

        result = backend_obj._invoice_has_blocked_payment(cursor, uid, pol, fact)

        self.assertTrue(result)

    def test_hasBlockedPayment_false_when_not_cobrament_bloquejat(self):
        """Test blocked payment returns False when cobrament_bloquejat is False."""
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        fue_bs_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_bo_social_pending_state"
        )[1]

        pol = self._create_mock_pol(cobrament_bloquejat=False)
        fact = self._create_mock_fact(pending_state_id=fue_bs_id)

        result = backend_obj._invoice_has_blocked_payment(cursor, uid, pol, fact)

        self.assertFalse(result)

    def test_hasBlockedPayment_false_when_cobrament_bloquejat_but_no_pending_state(self):
        """Test blocked payment returns False when no pending_state."""
        cursor = self.cursor
        uid = self.uid

        backend_obj = self.pool.get("report.backend.invoice.email")

        pol = self._create_mock_pol(cobrament_bloquejat=True)
        fact = self._create_mock_fact(pending_state_id=None)

        result = backend_obj._invoice_has_blocked_payment(cursor, uid, pol, fact)

        self.assertFalse(result)

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_reclamacio_en_curs(self):
        """Test blocked payment returns True when cobrament_bloquejat + reclamacio_en_curs."""
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        r1_bs_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "reclamacio_en_curs_pending_state"
        )[1]

        pol = self._create_mock_pol(cobrament_bloquejat=True)
        fact = self._create_mock_fact(pending_state_id=r1_bs_id)

        result = backend_obj._invoice_has_blocked_payment(cursor, uid, pol, fact)

        self.assertTrue(result)

    def test_hasBlockedPayment_true_when_cobrament_bloquejat_and_default_reclamacio_en_curs(self):
        """Test blocked payment returns True when cobrament_bloquejat + default_reclamacio_en_curs.
        """
        cursor = self.cursor
        uid = self.uid

        imd_obj = self.pool.get("ir.model.data")
        backend_obj = self.pool.get("report.backend.invoice.email")

        r1_df_id = imd_obj.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "default_reclamacio_en_curs_pending_state"
        )[1]

        pol = self._create_mock_pol(cobrament_bloquejat=True)
        fact = self._create_mock_fact(pending_state_id=r1_df_id)

        result = backend_obj._invoice_has_blocked_payment(cursor, uid, pol, fact)

        self.assertTrue(result)

    def test_hasBlockedPayment_false_when_pending_state_not_in_blocked_list(self):
        """Test blocked payment returns False when pending_state not in blocked list."""
        cursor = self.cursor
        uid = self.uid

        # Use an arbitrary ID not in blocked list
        backend_obj = self.pool.get("report.backend.invoice.email")

        # Use ID 99999 which is definitely NOT in blocked list
        not_blocked_id = 99999

        pol = self._create_mock_pol(cobrament_bloquejat=True)
        fact = self._create_mock_fact(pending_state_id=not_blocked_id)

        result = backend_obj._invoice_has_blocked_payment(cursor, uid, pol, fact)

        self.assertFalse(result)
