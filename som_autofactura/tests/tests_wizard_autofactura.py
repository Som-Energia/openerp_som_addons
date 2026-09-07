# -*- coding: utf-8 -*-
from destral import testing
from osv import osv
import mock
from som_autofactura import som_autofactura_task
from som_autofactura.wizard import wizard_autofactura


class TestsAutofacturaTaskTransactions(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestsAutofacturaTaskTransactions, self).setUp()
        self.task_obj = self.openerp.pool.get("som.autofactura.task.step")

    @mock.patch.object(som_autofactura_task, "sleep")
    def test_wait_for_job_group_releases_transaction_between_polls(self, sleep_mock):
        cursor = mock.Mock()
        config_obj = self.openerp.pool.get("res.config")
        jobs_group_obj = self.openerp.pool.get("oorq.jobs.group")
        task = mock.Mock()
        task.function = "validar_button"
        task.autoworker_task_name = "Validar Lot"
        events = []

        cursor.commit.side_effect = lambda: events.append("commit")
        cursor.rollback.side_effect = lambda: events.append("rollback")
        sleep_mock.side_effect = lambda seconds: events.append("sleep")

        def search(*args, **kwargs):
            events.append("search")
            return [1] if events.count("search") == 1 else []

        with mock.patch.object(config_obj, "get", return_value=300), mock.patch.object(
            self.task_obj, "browse", return_value=task
        ), mock.patch.object(jobs_group_obj, "search", side_effect=search):
            self.task_obj._wait_until_task_done(cursor, self.uid, [1], {})

        self.assertEqual(
            events,
            ["commit", "sleep", "search", "rollback", "sleep", "search", "rollback"],
        )

    @mock.patch.object(som_autofactura_task, "sleep")
    def test_wait_for_draft_invoices_releases_transaction_after_poll(self, sleep_mock):
        cursor = mock.Mock()
        config_obj = self.openerp.pool.get("res.config")
        invoice_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        task = mock.Mock()
        task.function = "obrir_factures_button"
        events = []

        cursor.commit.side_effect = lambda: events.append("commit")
        cursor.rollback.side_effect = lambda: events.append("rollback")
        sleep_mock.side_effect = lambda seconds: events.append("sleep")

        def search(*args, **kwargs):
            events.append("search")
            return [1]

        with mock.patch.object(config_obj, "get", return_value=300), mock.patch.object(
            self.task_obj, "browse", return_value=task
        ), mock.patch.object(invoice_obj, "search", side_effect=search):
            self.task_obj._wait_until_task_done(cursor, self.uid, [1], {})

        self.assertEqual(events, ["search", "commit", "sleep", "search", "rollback"])


class TestsWizardAutofacturaUnlock(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestsWizardAutofacturaUnlock, self).setUp()
        self.wiz_obj = self.openerp.pool.get("wizard.autofactura")

    @mock.patch.object(wizard_autofactura, "setup_redis_connection")
    @mock.patch.object(wizard_autofactura, "StartedJobRegistry")
    def test_unlock__no_jobs__raises(self, mock_registry_cls, mock_setup_redis):
        mock_registry_cls.return_value.get_job_ids.return_value = []

        with self.assertRaises(osv.except_osv):
            self.wiz_obj.unlock(self.cursor, self.uid, [])

    @mock.patch.object(wizard_autofactura, "setup_redis_connection")
    @mock.patch.object(wizard_autofactura, "StartedJobRegistry")
    def test_unlock__multiple_jobs__raises(self, mock_registry_cls, mock_setup_redis):
        mock_registry_cls.return_value.get_job_ids.return_value = ["job-1", "job-2"]

        with self.assertRaises(osv.except_osv):
            self.wiz_obj.unlock(self.cursor, self.uid, [])

    @mock.patch.object(wizard_autofactura, "setup_redis_connection")
    @mock.patch.object(wizard_autofactura, "Job")
    @mock.patch.object(wizard_autofactura, "StartedJobRegistry")
    def test_unlock__one_job__deletes_and_closes(
        self, mock_registry_cls, mock_job_cls, mock_setup_redis
    ):
        mock_registry_cls.return_value.get_job_ids.return_value = ["job-1"]
        mock_job = mock.MagicMock()
        mock_job_cls.fetch.return_value = mock_job

        result = self.wiz_obj.unlock(self.cursor, self.uid, [])

        mock_job_cls.fetch.assert_called_once_with(
            "job-1", connection=mock_setup_redis.return_value)
        mock_job.delete.assert_called_once()
        self.assertEqual(result, {"type": "ir.actions.act_window_close"})
