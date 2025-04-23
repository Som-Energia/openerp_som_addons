# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from tools.translate import _
from ..models import report_test
import mock


class TestReportTest(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.rp_obj = self.openerp.pool.get('report.test')
        self.rpg_obj = self.openerp.pool.get('report.test.group')
        self.rep_obj = self.openerp.pool.get('ir.actions.report.xml')

    def tearDown(self):
        self.txn.stop()

    def create_report_test_group(self, data):
        if 'name' in data and len(data.keys()) == 1:
            ids = self.rpg_obj.search(self.cursor, self.uid, [
                ('name', 'like', '%{}%'.format(data['name']))
            ])
            if ids:
                return ids[0]

        if 'name' not in data:
            data['name'] = "default report test group"

        if 'description' not in data:
            data['description'] = "default report test group desctiption"

        if 'priority' not in data:
            data['priority'] = 100

        if 'order' in data:
            data['priority'] = int(data['order'])

        if 'active' not in data:
            data['active'] = True

        return self.rpg_obj.create(self.cursor, self.uid, data)

    def create_report_test(self, data):
        if 'name' not in data:
            data['name'] = "default report test"

        if 'description' not in data:
            data['description'] = "default report test desctiption"

        if 'priority' not in data:
            data['priority'] = 100

        if 'order' in data:
            data['priority'] = int(data['order'])

        if 'active' not in data:
            data['active'] = True

        if 'result_log' not in data:
            data['result_log'] = ""

        if 'log' in data:
            data['result_log'] = data['log']

        if 'value' not in data:
            data['value'] = '1'

        if 'report_name' in data:
            rep_id = self.rep_obj.search(self.cursor, self.uid, [
                ('name', 'like', '%{}%'.format(data['report_name']))
            ])[0]
            data['report'] = rep_id

        if 'report' not in data:
            rep_id = self.rep_obj.search(self.cursor, self.uid, [
                ('name', 'like', '%Report%')
            ])[0]
            data['report'] = rep_id

        if 'interpreter' not in data:
            data['interpreter'] = "id"

        if 'group' in data:
            data['group_id'] = self.create_report_test_group(data['group'])

        if 'group_name' in data:
            data['group_id'] = self.create_report_test_group({'name': data['group_name']})

        if 'group_id' not in data:
            data['group_id'] = self.create_report_test_group({})

        if 'result' not in data:
            data['result'] = "pending"

        return self.rp_obj.create(self.cursor, self.uid, data)

    @mock.patch.object(report_test.ReportTest, "_compare_pdf")
    @mock.patch.object(report_test.ReportTest, "_generate_pdf")
    def test__execute_one_test__error_on_pdf(self, mock_generate_pdf, mock_compare_pdf):
        result_pdf = "Error generating pdf\n\ndoes not work"
        diff_pdf = "The diff content"
        mock_generate_pdf.return_value = False, result_pdf
        mock_compare_pdf.return_value = False, diff_pdf
        rp_id = self.create_report_test({})

        msg = self.rp_obj.execute_one_test(self.cursor, self.uid, rp_id, {})

        rp = self.rp_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(msg, _("Error generant pdf"))
        self.assertEqual(rp.result, "pdf_error")
        self.assertEqual(rp.result_log, result_pdf)

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, None)
        self.assertEqual(diff, None)
        self.assertEqual(expected, None)

    @mock.patch.object(report_test.ReportTest, "_compare_pdf")
    @mock.patch.object(report_test.ReportTest, "_generate_pdf")
    def test__execute_one_test__pdf_ok_noexpected(self, mock_generate_pdf, mock_compare_pdf):
        result_pdf = "The pdf contents"
        diff_pdf = "The diff content"
        mock_generate_pdf.return_value = True, result_pdf
        mock_compare_pdf.return_value = False, diff_pdf
        rp_id = self.create_report_test({})

        msg = self.rp_obj.execute_one_test(self.cursor, self.uid, rp_id, {})

        rp = self.rp_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(msg, _("Sense original per comprovar"))
        self.assertEqual(rp.result, "no_expected")

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, result_pdf)
        self.assertEqual(diff, None)
        self.assertEqual(expected, None)

    @mock.patch.object(report_test.ReportTest, "_compare_pdf")
    @mock.patch.object(report_test.ReportTest, "_generate_pdf")
    def test__execute_one_test__diferents(self, mock_generate_pdf, mock_compare_pdf):
        result_pdf = "The pdf contents"
        diff_pdf = "The diff content"
        expected_pdf = "The original pdf"
        mock_generate_pdf.return_value = True, result_pdf
        mock_compare_pdf.return_value = False, diff_pdf
        rp_id = self.create_report_test({})
        self.rp_obj._store_expected_attachment(self.cursor, self.uid, rp_id, expected_pdf)

        msg = self.rp_obj.execute_one_test(self.cursor, self.uid, rp_id, {})

        rp = self.rp_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(msg, _("Diferències trobades"))
        self.assertEqual(rp.result, "differents")

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, result_pdf)
        self.assertEqual(diff, diff_pdf)
        self.assertEqual(expected, expected_pdf)

    @mock.patch.object(report_test.ReportTest, "_compare_pdf")
    @mock.patch.object(report_test.ReportTest, "_generate_pdf")
    def test__execute_one_test__equals(self, mock_generate_pdf, mock_compare_pdf):
        result_pdf = "The pdf contents"
        expected_pdf = "The original pdf"
        mock_generate_pdf.return_value = True, result_pdf
        mock_compare_pdf.return_value = True, None
        rp_id = self.create_report_test({})
        self.rp_obj._store_expected_attachment(self.cursor, self.uid, rp_id, expected_pdf)

        msg = self.rp_obj.execute_one_test(self.cursor, self.uid, rp_id, {})

        rp = self.rp_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(msg, _("Identics, sense canvis"))
        self.assertEqual(rp.result, "equals")

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, None)
        self.assertEqual(diff, None)
        self.assertEqual(expected, expected_pdf)

    def test__accept_one_test__ok(self):
        result_pdf = "The pdf contents"
        expected_pdf = "The original pdf"
        rp_id = self.create_report_test({})
        self.rp_obj._store_expected_attachment(self.cursor, self.uid, rp_id, expected_pdf)
        self.rp_obj._store_result_attachment(self.cursor, self.uid, rp_id, result_pdf)

        msg = self.rp_obj.accept_one_test(self.cursor, self.uid, rp_id, {})

        rp = self.rp_obj.browse(self.cursor, self.uid, rp_id)
        self.assertEqual(msg, _("Fitxer acceptat"))
        self.assertEqual(rp.result, "equals")

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, None)
        self.assertEqual(diff, None)
        self.assertEqual(expected, result_pdf)

    def test__accept_one_test__no_result(self):
        expected_pdf = "The original pdf"
        rp_id = self.create_report_test({})
        self.rp_obj._store_expected_attachment(self.cursor, self.uid, rp_id, expected_pdf)

        msg = self.rp_obj.accept_one_test(self.cursor, self.uid, rp_id, {})

        self.assertEqual(msg, _("Res per acceptar / Ja acceptat"))

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, None)
        self.assertEqual(expected, expected_pdf)

    def test__accept_one_test__no_files(self):
        rp_id = self.create_report_test({})

        msg = self.rp_obj.accept_one_test(self.cursor, self.uid, rp_id, {})

        self.assertEqual(msg, _("Error sense fitxers!"))

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, None)
        self.assertEqual(expected, None)

    def test__files__some_operations(self):
        result_pdf = "The pdf contents"
        diff_pdf = "The diff content"
        expected_pdf = "The original pdf"
        rp_id = self.create_report_test({})

        exists_expected = self.rp_obj._exists_expected_attachment(self.cursor, self.uid, rp_id)
        self.assertEqual(bool(exists_expected), False)

        self.rp_obj._store_result_attachment(self.cursor, self.uid, rp_id, result_pdf)
        self.rp_obj._store_diff_attachment(self.cursor, self.uid, rp_id, diff_pdf)
        self.rp_obj._store_expected_attachment(self.cursor, self.uid, rp_id, expected_pdf)

        exists_expected = self.rp_obj._exists_expected_attachment(self.cursor, self.uid, rp_id)
        self.assertEqual(bool(exists_expected), True)

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, result_pdf)
        self.assertEqual(diff, diff_pdf)
        self.assertEqual(expected, expected_pdf)

        self.rp_obj._del_result_attachment(self.cursor, self.uid, rp_id)

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, None)
        self.assertEqual(diff, diff_pdf)
        self.assertEqual(expected, expected_pdf)

        self.rp_obj._del_diff_attachment(self.cursor, self.uid, rp_id)

        result = self.rp_obj._get_result_attachment(self.cursor, self.uid, rp_id, {})
        diff = self.rp_obj._get_diff_attachment(self.cursor, self.uid, rp_id, {})
        expected = self.rp_obj._get_expected_attachment(self.cursor, self.uid, rp_id, {})
        self.assertEqual(result, None)
        self.assertEqual(diff, None)
        self.assertEqual(expected, expected_pdf)

    def test___get_resource_id___id(self):
        value_id = 123456
        rp_id = self.create_report_test({
            'interpreter': 'id',
            'value': str(value_id),
        })

        res_id, msg = self.rp_obj._get_resource_id(self.cursor, self.uid, rp_id, {})

        self.assertEqual(res_id, value_id)
        self.assertEqual(msg, _(""))
