# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from yamlns.testutils import assertNsEqual


class TestPendingStatesData(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def getref(self, module, reference):
        IrModelData = self.pool.get("ir.model.data")
        return IrModelData.get_object_reference(self.cursor, self.uid, module, reference)[1]

    def test_dataInserted(self):
        id = self.getref(
            "som_account_invoice_pending", "default_pendent_traspas_advocats_pending_state"
        )
        self.assertTrue(id)
        PendingState = self.pool.get("account.invoice.pending.state")
        pendingState = PendingState.read(self.cursor, self.uid, id, [])
        pendingState["process_id"] = pendingState["process_id"][1]
        assertNsEqual(
            self,
            pendingState,
            """\
            id: {id}
            active: true
            is_last: true
            template_id: false
            name: Pendent consulta advocats
            pending_days: 0
            pending_days_type: natural
            process_id: Default Process
            weight: 1108
        """.format(
                id=id
            ),
        )


# vim: et ts=4 sw=4
