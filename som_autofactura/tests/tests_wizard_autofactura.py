# -*- coding: utf-8 -*-
from destral import testing
from osv import osv
import mock
from som_autofactura.wizard import wizard_autofactura


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
