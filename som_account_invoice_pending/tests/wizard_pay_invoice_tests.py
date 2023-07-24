# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import date
import mock
from giscedata_facturacio.wizard import wizard_pay_invoice
from som_account_invoice_pending.wizard import wizard_pay_invoice as som_wizard_pay_invoice


class TestWizardPayInvoice(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool

    def _load_data_unpaid_invoice(self, cursor, uid):
        imd_obj = self.pool.get("ir.model.data")
        self.inv_obj = self.pool.get("account.invoice")
        self.fact_obj = self.pool.get("giscedata.facturacio.factura")
        self.pay_inv_obj = self.pool.get("facturacio.pay.invoice")
        self.cfg_obj = self.pool.get("res.config")

        self.waiting_48h_def = imd_obj.get_object_reference(
            cursor,
            uid,
            "som_account_invoice_pending",
            "default_pendent_notificacio_tall_imminent_pending_state",
        )[1]
        self.tall_def = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "default_tall_pending_state"
        )[1]

        self.fact_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]

        self.tpv_journal_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "tpv_journal"
        )[1]

        self.other_journal_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "other_journal"
        )[1]

        self.account_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "cobraments_mail_account"
        )[1]

    @mock.patch.object(wizard_pay_invoice.WizardPayInvoice, "action_pay_and_reconcile")
    @mock.patch.object(som_wizard_pay_invoice.WizardPayInvoice, "action_mail_avis_cobraments_async")
    def test__action_pay_and_reconcile__other_journal__not_notified(
        self, mocked_action_mail_avis_cobraments_async, mocked_pay_and_rec
    ):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self._load_data_unpaid_invoice(cursor, uid)

            ctx = {"active_id": self.fact_id, "active_ids": [self.fact_id]}

            today = date.today().strftime("%Y%m%d")
            vals = {
                "comment": "Pagament efectuat des de la OV. {}".format(today),
                "journal_id": self.other_journal_id,
            }

            pay_invoice_wizard = self.pay_inv_obj.create(cursor, uid, vals, context=ctx)
            wiz_id = pay_invoice_wizard
            self.pay_inv_obj.action_pay_and_reconcile(cursor, uid, wiz_id, context=ctx)

            mocked_pay_and_rec.assert_called_once()
            mocked_action_mail_avis_cobraments_async.assert_not_called()

    @mock.patch.object(wizard_pay_invoice.WizardPayInvoice, "action_pay_and_reconcile")
    @mock.patch.object(som_wizard_pay_invoice.WizardPayInvoice, "action_mail_avis_cobraments_async")
    def test__action_pay_and_reconcile__other_journal_other_ps__not_notified(
        self, mocked_action_mail_avis_cobraments_async, mocked_pay_and_rec
    ):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self._load_data_unpaid_invoice(cursor, uid)
            self.fact_obj.set_pending(cursor, uid, [self.fact_id], self.waiting_48h_def)
            self.cfg_obj.set(
                cursor, uid, "pay_alert_pending_states_som", "[{}]".format(self.tall_def)
            )

            ctx = {"active_id": self.fact_id, "active_ids": [self.fact_id]}

            today = date.today().strftime("%Y%m%d")
            vals = {
                "comment": "Pagament efectuat des de la OV. {}".format(today),
                "journal_id": self.other_journal_id,
            }

            pay_invoice_wizard = self.pay_inv_obj.create(cursor, uid, vals, context=ctx)
            wiz_id = pay_invoice_wizard
            self.pay_inv_obj.action_pay_and_reconcile(cursor, uid, wiz_id, context=ctx)

            mocked_pay_and_rec.assert_called_once()
            mocked_action_mail_avis_cobraments_async.assert_not_called()

    @mock.patch.object(wizard_pay_invoice.WizardPayInvoice, "action_pay_and_reconcile")
    @mock.patch.object(som_wizard_pay_invoice.WizardPayInvoice, "action_mail_avis_cobraments_async")
    def test__action_pay_and_reconcile__other_journal_tall_ps__not_notified(
        self, mocked_action_mail_avis_cobraments_async, mocked_pay_and_rec
    ):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self._load_data_unpaid_invoice(cursor, uid)
            self.fact_obj.set_pending(cursor, uid, [self.fact_id], self.tall_def)
            self.cfg_obj.set(
                cursor, uid, "pay_alert_pending_states_som", "[{}]".format(self.tall_def)
            )

            ctx = {"active_id": self.fact_id, "active_ids": [self.fact_id]}

            today = date.today().strftime("%Y%m%d")
            vals = {
                "comment": "Pagament efectuat des de la OV. {}".format(today),
                "journal_id": self.other_journal_id,
            }

            pay_invoice_wizard = self.pay_inv_obj.create(cursor, uid, vals, context=ctx)
            wiz_id = pay_invoice_wizard
            self.pay_inv_obj.action_pay_and_reconcile(cursor, uid, wiz_id, context=ctx)

            mocked_pay_and_rec.assert_called_once()
            mocked_action_mail_avis_cobraments_async.assert_not_called()

    @mock.patch.object(wizard_pay_invoice.WizardPayInvoice, "action_pay_and_reconcile")
    @mock.patch.object(som_wizard_pay_invoice.WizardPayInvoice, "action_mail_avis_cobraments_async")
    def test__action_pay_and_reconcile__tpv_journal_other_ps__not_notified(
        self, mocked_action_mail_avis_cobraments_async, mocked_pay_and_rec
    ):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self._load_data_unpaid_invoice(cursor, uid)
            self.fact_obj.set_pending(cursor, uid, [self.fact_id], self.waiting_48h_def)
            self.cfg_obj.set(
                cursor, uid, "pay_alert_pending_states_som", "[{}]".format(self.tall_def)
            )

            ctx = {"active_id": self.fact_id, "active_ids": [self.fact_id]}

            today = date.today().strftime("%Y%m%d")
            vals = {
                "comment": "Pagament efectuat des de la OV. {}".format(today),
                "journal_id": self.tpv_journal_id,
            }

            pay_invoice_wizard = self.pay_inv_obj.create(cursor, uid, vals, context=ctx)
            wiz_id = pay_invoice_wizard
            self.pay_inv_obj.action_pay_and_reconcile(cursor, uid, wiz_id, context=ctx)

            mocked_pay_and_rec.assert_called_once()
            mocked_action_mail_avis_cobraments_async.assert_not_called()

    @mock.patch.object(wizard_pay_invoice.WizardPayInvoice, "action_pay_and_reconcile")
    @mock.patch.object(som_wizard_pay_invoice.WizardPayInvoice, "action_mail_avis_cobraments_async")
    def test__action_pay_and_reconcile__tpv_journal_tall_ps__notified(
        self, mocked_action_mail_avis_cobraments_async, mocked_pay_and_rec
    ):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self._load_data_unpaid_invoice(cursor, uid)

            self.fact_obj.set_pending(cursor, uid, [self.fact_id], self.tall_def)
            self.cfg_obj.set(
                cursor, uid, "pay_alert_pending_states_som", "[{}]".format(self.tall_def)
            )

            ctx = {"active_id": self.fact_id, "active_ids": [self.fact_id]}

            today = date.today().strftime("%Y%m%d")
            vals = {
                "comment": "Pagament efectuat des de la OV. {}".format(today),
                "journal_id": self.tpv_journal_id,
            }

            pay_invoice_wizard = self.pay_inv_obj.create(cursor, uid, vals, context=ctx)
            wiz_id = pay_invoice_wizard
            self.pay_inv_obj.action_pay_and_reconcile(cursor, uid, wiz_id, context=ctx)

            mocked_pay_and_rec.assert_called_once()
            mocked_action_mail_avis_cobraments_async.assert_called()

    @mock.patch.object(wizard_pay_invoice.WizardPayInvoice, "action_pay_and_reconcile")
    @mock.patch.object(som_wizard_pay_invoice.WizardPayInvoice, "action_mail_avis_cobraments_async")
    def test__action_mail_avis_cobraments__ok(
        self, mocked_action_mail_avis_cobraments_async, mocked_pay_and_rec
    ):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self._load_data_unpaid_invoice(cursor, uid)

            self.fact_obj.set_pending(cursor, uid, [self.fact_id], self.tall_def)
            self.cfg_obj.set(
                cursor, uid, "pay_alert_pending_states_som", "[{}]".format(self.tall_def)
            )

            ctx = {"active_id": self.fact_id, "active_ids": [self.fact_id]}

            today = date.today().strftime("%Y%m%d")
            vals = {
                "comment": "Pagament efectuat des de la OV. {}".format(today),
                "journal_id": self.tpv_journal_id,
            }

            pay_invoice_wizard = self.pay_inv_obj.create(cursor, uid, vals, context=ctx)
            wiz_id = pay_invoice_wizard
            self.pay_inv_obj.action_pay_and_reconcile(cursor, uid, wiz_id, context=ctx)

            mocked_pay_and_rec.assert_called_once()
            mocked_action_mail_avis_cobraments_async.assert_called()
