# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64

from destral import testing
from destral.transaction import Transaction
from osv import osv


class TestReportTestCsv(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.groups = self.openerp.pool.get('report.test.group')
        self.tests = self.openerp.pool.get('report.test')
        self.wizards = self.openerp.pool.get('wizard.report.test.group.csv')
        self.reports = self.openerp.pool.get('ir.actions.report.xml')
        self.report_id = self.reports.create(self.cursor, self.uid, {
            'name': 'CSV regression report',
            'report_name': 'report_tester.csv_regression',
            'model': 'res.partner',
        })

    def tearDown(self):
        self.txn.stop()

    def _create_group(self, name='CSV source group'):
        return self.groups.create(self.cursor, self.uid, {
            'name': name, 'priority': 100,
        })

    def _create_test(self, group_id, **overrides):
        values = {
            'name': 'CSV source test', 'priority': 100, 'active': True,
            'group_id': group_id, 'report': self.report_id,
            'interpreter': 'id', 'value': '123', 'result': 'equals',
        }
        values.update(overrides)
        return self.tests.create(self.cursor, self.uid, values)

    def _create_import(self, content, **overrides):
        values = {
            'operation': 'import', 'group_name': 'CSV imported group',
            'report': self.report_id, 'interpreter': 'id',
            'csv_file': base64.b64encode(content),
        }
        values.update(overrides)
        return self.wizards.create(self.cursor, self.uid, values, context={})

    def _test_ids(self, group_id):
        return self.tests.search(
            self.cursor, self.uid, [('group_id', '=', group_id)],
            order='priority,id', context={'active_test': False}
        )

    def _definitions(self, group_id):
        rows = self.tests.read(self.cursor, self.uid, self._test_ids(group_id), [
            'name', 'description', 'priority', 'active', 'report',
            'interpreter', 'value',
        ], context={'active_test': False})
        for row in rows:
            del row['id']
            row['report'] = row['report'][0]
            row['description'] = row['description'] or ''
        return sorted(rows, key=lambda row: (row['priority'], row['name'], row['value']))

    def _record_ids(self):
        context = {'active_test': False}
        return (
            self.groups.search(self.cursor, self.uid, [], context=context),
            self.tests.search(self.cursor, self.uid, [], context=context),
        )

    def test_export_reimport_preserves_test_definitions(self):
        source_id = self._create_group()
        other_report = self.reports.create(self.cursor, self.uid, {
            'name': 'Alternative CSV report',
            'report_name': 'report_tester.csv_alternative',
            'model': 'res.company',
        })
        first_id = self._create_test(
            source_id, name=u'Factura "d\'estiu", amb accents: àèíòú',
            description=u'Primera línia, amb "cometes";\nSegona línia: ç',
            value='00123', priority=10,
        )
        self._create_test(
            source_id, name=u'Factura inactiva, "revisió"',
            description=u'No s\'ha d\'ometre en exportar.',
            active=False, interpreter='id_fact', value='F2026/000123',
            report=other_report, priority=20,
        )
        self._create_test(source_id, interpreter='id_pol', value='0001234', priority=30)
        self._create_test(source_id, interpreter='fact_pol', value='0005678', priority=40)
        attachment_obj = self.openerp.pool.get('ir.attachment')
        attachment_obj.create(self.cursor, self.uid, {
            'name': 'expected.pdf', 'datas_fname': 'expected.pdf',
            'datas': base64.b64encode(b'%PDF-source-reference'),
            'res_model': 'report.test', 'res_id': first_id,
        })
        export_id = self.wizards.create(self.cursor, self.uid, {
            'operation': 'export', 'group_id': source_id,
        }, context={})

        self.wizards.export_csv(self.cursor, self.uid, [export_id])
        exported = self.wizards.read(self.cursor, self.uid, [export_id], ['output_file'])[0]
        import_id = self._create_import(
            base64.b64decode(exported['output_file']), report=False
        )
        self.wizards.import_csv(self.cursor, self.uid, [import_id])

        imported = self.wizards.read(self.cursor, self.uid, [import_id], ['group_id', 'state'])[0]
        target_id = imported['group_id']
        self.assertNotEqual(target_id, source_id)
        self.assertEqual(imported['state'], 'end')
        self.assertEqual(self._definitions(target_id), self._definitions(source_id))
        imported_ids = self._test_ids(target_id)
        self.assertEqual(len(imported_ids), 4)
        self.assertEqual(
            [row['result'] for row in self.tests.read(
                self.cursor, self.uid, imported_ids, ['result'],
                context={'active_test': False}
            )],
            ['pending'] * 4,
        )
        self.assertEqual(attachment_obj.search(self.cursor, self.uid, [
            ('res_model', '=', 'report.test'), ('res_id', 'in', imported_ids),
        ]), [])

    def test_import_appends_without_changing_existing_tests(self):
        group_id = self._create_group()
        original_id = self._create_test(group_id, active=False)
        original = self._definitions(group_id)
        wizard_id = self._create_import(b'value\n456\n789\n', group_id=group_id)

        self.wizards.import_csv(self.cursor, self.uid, [wizard_id])

        all_ids = self._test_ids(group_id)
        self.assertEqual(len(all_ids), 3)
        self.assertIn(original_id, all_ids)
        rows = self._definitions(group_id)
        self.assertEqual(rows[0], original[0])
        self.assertEqual([row['priority'] for row in rows], [100, 110, 120])
        self.assertEqual([row['value'] for row in rows], ['123', '456', '789'])
        self.assertEqual([row['report'] for row in rows], [self.report_id] * 3)
        self.assertEqual([row['interpreter'] for row in rows], ['id'] * 3)

    def test_invalid_row_does_not_create_group_or_tests(self):
        wizard_id = self._create_import(b'value\n123\nnot-an-id\n')
        before = self._record_ids()

        with self.assertRaises(osv.except_osv) as raised:
            self.wizards.import_csv(self.cursor, self.uid, [wizard_id])

        self.assertIn(u'Línia 3', u'{}'.format(raised.exception))
        self.assertEqual(self._record_ids(), before)
        wizard = self.wizards.read(self.cursor, self.uid, [wizard_id], ['group_id', 'state'])[0]
        self.assertFalse(wizard['group_id'])
        self.assertEqual(wizard['state'], 'init')

    def test_invalid_row_does_not_change_existing_group(self):
        group_id = self._create_group()
        self._create_test(group_id)
        original = self._definitions(group_id)
        before = self._record_ids()
        wizard_id = self._create_import(b'value\n456\nnot-an-id\n', group_id=group_id)

        with self.assertRaises(osv.except_osv):
            self.wizards.import_csv(self.cursor, self.uid, [wizard_id])

        self.assertEqual(self._record_ids(), before)
        self.assertEqual(self._definitions(group_id), original)

    def test_import_supports_delimiters_and_per_row_options(self):
        for separator in [',', ';', '\t']:
            content = separator.join([
                'value', 'interpreter', 'report_name', 'report_model', 'active', 'priority',
            ]) + '\n' + separator.join([
                '0001234', 'id_pol', 'report_tester.csv_regression', 'res.partner', '0', '7',
            ]) + '\n'
            wizard_id = self._create_import(content.encode('utf-8'), report=False)

            self.wizards.import_csv(self.cursor, self.uid, [wizard_id])

            wizard = self.wizards.read(self.cursor, self.uid, [wizard_id], ['group_id'])[0]
            row = self._definitions(wizard['group_id'])[0]
            self.assertEqual(row['value'], '0001234')
            self.assertEqual(row['interpreter'], 'id_pol')
            self.assertEqual(row['report'], self.report_id)
            self.assertEqual(row['priority'], 7)
            self.assertFalse(row['active'])

    def test_malformed_csv_does_not_create_records(self):
        before = self._record_ids()
        for content in [
            b'value\n', b'id\n123\n', b'value,value\n123,456\n',
            b'value,name\n123,test,extra\n', b'value\n\xff\n',
        ]:
            wizard_id = self._create_import(content)
            with self.assertRaises(osv.except_osv):
                self.wizards.import_csv(self.cursor, self.uid, [wizard_id])
            self.assertEqual(self._record_ids(), before)
