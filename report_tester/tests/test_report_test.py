# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction
from tools.translate import _
from lxml import etree
from ..models import report_test
import json
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

    def test_default_tree_does_not_autorefresh(self):
        view = self.rp_obj.fields_view_get(
            self.cursor, self.uid, view_type='tree'
        )
        tree = etree.fromstring(view['arch'])
        result_fields = tree.xpath("./field[@name='result']")

        self.assertEqual(len(result_fields), 1)
        self.assertIsNone(result_fields[0].get('autorefresh'))

    def test_group_running_indicator_tracks_active_tests(self):
        group_id = self.create_report_test_group({})
        self.assertFalse(self.rpg_obj.read(
            self.cursor, self.uid, group_id, ['has_running_tests']
        )['has_running_tests'])
        self.create_report_test({
            'group_id': group_id, 'result': 'doing', 'active': False,
        })
        test_id = self.create_report_test({'group_id': group_id})

        for state in ['pending', 'doing', 'equals', 'differents',
                      'pdf_error', 'no_expected', 'error']:
            self.rp_obj.write(self.cursor, self.uid, test_id, {'result': state})
            group = self.rpg_obj.read(
                self.cursor, self.uid, group_id, ['has_running_tests'],
                context={'active_test': False}
            )
            self.assertEqual(group['has_running_tests'], state == 'doing')

    def test_group_running_indicator_is_group_scoped(self):
        idle_group = self.create_report_test_group({})
        busy_group = self.create_report_test_group({})
        self.create_report_test({'group_id': idle_group, 'result': 'equals'})
        self.create_report_test({'group_id': busy_group, 'result': 'equals'})
        self.create_report_test({'group_id': busy_group, 'result': 'doing'})

        groups = self.rpg_obj.read(
            self.cursor, self.uid, [idle_group, busy_group],
            ['has_running_tests']
        )

        self.assertEqual(
            dict((group['id'], group['has_running_tests']) for group in groups),
            {idle_group: False, busy_group: True}
        )

    def test_queued_tests_enable_group_refresh(self):
        group_id = self.create_report_test_group({})
        test_id = self.create_report_test({'group_id': group_id})

        queued_ids = self.rpg_obj.pre_execute_tests_async(
            self.cursor, self.uid, [group_id]
        )

        self.assertEqual(queued_ids, [test_id])
        self.assertTrue(self.rpg_obj.read(
            self.cursor, self.uid, group_id, ['has_running_tests']
        )['has_running_tests'])

    def test_live_list_contains_the_same_group_tests(self):
        group_id = self.create_report_test_group({})
        test_id = self.create_report_test({'group_id': group_id})
        inactive_id = self.create_report_test({
            'group_id': group_id, 'active': False,
        })
        other_group = self.create_report_test_group({})
        self.create_report_test({'group_id': other_group})

        group = self.rpg_obj.read(
            self.cursor, self.uid, group_id, ['test_ids', 'live_test_ids'],
            context={'active_test': False}
        )

        self.assertEqual(set(group['test_ids']), set([test_id, inactive_id]))
        self.assertEqual(set(group['live_test_ids']), set(group['test_ids']))

    def test_group_view_only_refreshes_the_live_list(self):
        view = self.rpg_obj.fields_view_get(
            self.cursor, self.uid, view_type='form'
        )
        form = etree.fromstring(view['arch'])
        control = form.xpath(".//field[@name='has_running_tests']")[0]
        self.assertEqual(control.get('autorefresh'), '1')
        self.assertEqual(control.get('invisible'), '1')

        for field_name, hidden_when in [('test_ids', True),
                                        ('live_test_ids', False)]:
            field = form.xpath(".//field[@name='{}']".format(field_name))[0]
            condition = json.loads(field.get('json_attrs'))['invisible']
            self.assertEqual(condition['rules'], [{
                'field': 'has_running_tests', 'operator': '=',
                'value': hidden_when,
            }])

        live_tree = etree.fromstring(
            view['fields']['live_test_ids']['views']['tree']['arch']
        )
        self.assertEqual(
            live_tree.xpath("./field[@name='result']")[0].get('autorefresh'),
            '1'
        )
