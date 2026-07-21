# -*- coding: utf-8 -*-
from __future__ import absolute_import
import imp
import os
import shutil
import tempfile

import mock
import netsvc
import pypdftk
from destral import testing
from destral.transaction import Transaction

_netsvc_local_service = (
    'som_polissa_condicions_generals.report.'
    'giscedata_polissa_contract_summary_full.netsvc.LocalService'
)
_pypdftk_concat = (
    'som_polissa_condicions_generals.report.'
    'giscedata_polissa_contract_summary_full.pypdftk.concat'
)
_os_fdopen = (
    'som_polissa_condicions_generals.report.'
    'giscedata_polissa_contract_summary_full.os.fdopen'
)


class TestContractSummaryFullReport(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.report = netsvc.LocalService(
            'report.giscedata.polissa.contract.summary.full'
        )._service

    def tearDown(self):
        self.txn.stop()

    @mock.patch(_netsvc_local_service)
    def test_create_renders_summary_then_contract_with_same_arguments(
        self, mock_local_service
    ):
        summary_service = mock.Mock()
        contract_service = mock.Mock()
        summary_service.create.return_value = (b'summary', 'pdf')
        contract_service.create.return_value = (b'contract', 'pdf')
        mock_local_service.side_effect = [summary_service, contract_service]
        ids = [42]
        datas = {'form': {'date': '2026-07-21'}}
        context = {'lang': 'ca_ES'}

        with mock.patch.object(
            self.report, 'join_pdfs', return_value=b'merged'
        ) as join_pdfs:
            result = self.report.create(
                self.cursor, self.uid, ids, datas, context
            )

        self.assertEqual(result, (b'merged', 'pdf'))
        self.assertEqual(mock_local_service.call_args_list, [
            mock.call('report.giscedata.polissa.contract.summary'),
            mock.call('report.giscedata.polissa'),
        ])
        self.assertEqual(summary_service.create.call_args_list, [
            mock.call(self.cursor, self.uid, ids, datas, context),
        ])
        self.assertEqual(contract_service.create.call_args_list, [
            mock.call(self.cursor, self.uid, ids, datas, context),
        ])
        join_pdfs.assert_called_once_with([b'summary', b'contract'])

    @mock.patch(_pypdftk_concat)
    def test_join_pdfs_merges_summary_before_contract_and_removes_files(
        self, mock_concat
    ):
        temporary_directory = tempfile.mkdtemp()
        merged_path = os.path.join(temporary_directory, 'merged.pdf')

        def concat(files):
            with open(merged_path, 'wb') as merged_file:
                for pdf_path in files:
                    with open(pdf_path, 'rb') as pdf_file:
                        merged_file.write(pdf_file.read())
            return merged_path

        mock_concat.side_effect = concat
        original_mkstemp = tempfile.mkstemp

        def mkstemp(suffix):
            return original_mkstemp(suffix=suffix, dir=temporary_directory)

        try:
            with mock.patch(
                'som_polissa_condicions_generals.report.'
                'giscedata_polissa_contract_summary_full.tempfile.mkstemp',
                side_effect=mkstemp,
            ):
                result = self.report.join_pdfs([b'summary', b'contract'])
            pdf_paths = mock_concat.call_args[1]['files']
            self.assertFalse(os.path.exists(pdf_paths[0]))
            self.assertFalse(os.path.exists(pdf_paths[1]))
            self.assertFalse(os.path.exists(merged_path))
        finally:
            shutil.rmtree(temporary_directory)

        self.assertEqual(result, b'summarycontract')
        self.assertEqual(len(pdf_paths), 2)

    @mock.patch(_os_fdopen, side_effect=IOError('cannot open temporary PDF'))
    def test_join_pdfs_removes_path_when_opening_temporary_file_fails(
        self, mock_fdopen
    ):
        temporary_directory = tempfile.mkdtemp()
        original_mkstemp = tempfile.mkstemp

        def mkstemp(suffix):
            return original_mkstemp(suffix=suffix, dir=temporary_directory)

        try:
            with mock.patch(
                'som_polissa_condicions_generals.report.'
                'giscedata_polissa_contract_summary_full.tempfile.mkstemp',
                side_effect=mkstemp,
            ):
                with self.assertRaises(IOError):
                    self.report.join_pdfs([b'summary'])
            self.assertEqual(os.listdir(temporary_directory), [])
        finally:
            shutil.rmtree(temporary_directory)

        self.assertTrue(mock_fdopen.called)

    def test_join_pdfs_returns_valid_two_page_pdf(self):
        merged_pdf = self.report.join_pdfs([
            self._build_pdf('summary-page'),
            self._build_pdf('contract-page'),
        ])
        file_descriptor, merged_path = tempfile.mkstemp(suffix='.pdf')
        try:
            with os.fdopen(file_descriptor, 'wb') as merged_file:
                merged_file.write(merged_pdf)

            self.assertEqual(pypdftk.get_num_pages(merged_path), 2)
        finally:
            if os.path.exists(merged_path):
                os.remove(merged_path)

    def _build_pdf(self, label):
        content = 'BT /F1 24 Tf 72 100 Td ({0}) Tj ET'.format(label)
        objects = [
            '<< /Type /Catalog /Pages 2 0 R >>',
            '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] '
            '/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
            '<< /Length {0} >>\nstream\n{1}\nendstream'.format(
                len(content), content
            ),
            '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        ]
        pdf = '%PDF-1.4\n'
        offsets = []
        for object_number, pdf_object in enumerate(objects, 1):
            offsets.append(len(pdf))
            pdf += '{0} 0 obj\n{1}\nendobj\n'.format(
                object_number, pdf_object
            )

        xref_offset = len(pdf)
        pdf += 'xref\n0 {0}\n0000000000 65535 f \n'.format(len(objects) + 1)
        for offset in offsets:
            pdf += '{0:010d} 00000 n \n'.format(offset)
        pdf += 'trailer\n<< /Size {0} /Root 1 0 R >>\nstartxref\n{1}\n%%EOF\n'.format(
            len(objects) + 1, xref_offset
        )
        return pdf


class TestGiscedataPolissaContractSummaryRoutes(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.polissa_obj = self.openerp.pool.get('giscedata.polissa')
        self.report_obj = self.openerp.pool.get('ir.actions.report.xml')
        self.values_obj = self.openerp.pool.get('ir.values')
        self.imd_obj = self.openerp.pool.get('ir.model.data')

    def tearDown(self):
        self.txn.stop()

    def test_action_imprimir_contract_summary_pdf_uses_summary_report(self):
        result = self.polissa_obj.action_imprimir_contract_summary_pdf(
            self.cursor, self.uid, [1], context={}
        )

        self.assertEqual(
            result['report_name'],
            'giscedata.polissa.contract.summary'
        )

    def test_action_imprimir_contract_summary_full_pdf_uses_combined_report(self):
        result = self.polissa_obj.action_imprimir_contract_summary_full_pdf(
            self.cursor, self.uid, [1], context={}
        )

        self.assertEqual(
            result['report_name'],
            'giscedata.polissa.contract.summary.full'
        )

    def test_summary_report_service_is_registered(self):
        service = netsvc.LocalService(
            'report.giscedata.polissa.contract.summary'
        )

        self.assertEqual(
            service._service.name,
            'report.giscedata.polissa.contract.summary'
        )
        self.assertTrue(callable(service.create))

    def test_combined_report_service_is_registered(self):
        service = netsvc.LocalService(
            'report.giscedata.polissa.contract.summary.full'
        )

        self.assertEqual(
            service._service.name,
            'report.giscedata.polissa.contract.summary.full'
        )
        self.assertTrue(callable(service.create))

    def test_contract_summary_print_records_keep_both_routes(self):
        self._assert_summary_print_route()
        self._assert_combined_print_route()

    def test_migration_loads_only_combined_report_xml(self):
        migration = self._load_migration()

        with mock.patch.object(migration, 'load_data') as load_data:
            migration.up(self.cursor, '5.0.25.7')

        self.assertEqual(load_data.call_args_list, [
            mock.call(
                self.cursor,
                'som_polissa_condicions_generals',
                'report/giscedata_polissa_contract_summary_full_report.xml',
                idref=None,
                mode='update'
            ),
        ])

    def test_migration_creates_combined_route_without_replacing_summary(self):
        summary_action = self.imd_obj._get_obj(
            self.cursor,
            self.uid,
            'som_polissa_condicions_generals',
            'report_contract_summary'
        )
        summary_value = self.imd_obj._get_obj(
            self.cursor,
            self.uid,
            'som_polissa_condicions_generals',
            'value_report_contract_summary'
        )
        summary_action_data = self.report_obj.read(
            self.cursor, self.uid, summary_action.id, ['name', 'report_name']
        )
        summary_value_data = self.values_obj.read(
            self.cursor, self.uid, summary_value.id, ['model', 'name', 'value']
        )
        combined_action = self.imd_obj._get_obj(
            self.cursor,
            self.uid,
            'som_polissa_condicions_generals',
            'report_contract_summary_full'
        )
        combined_value = self.imd_obj._get_obj(
            self.cursor,
            self.uid,
            'som_polissa_condicions_generals',
            'value_report_contract_summary_full'
        )
        combined_imd_ids = self.imd_obj.search(self.cursor, self.uid, [
            ('module', '=', 'som_polissa_condicions_generals'),
            ('name', 'in', [
                'report_contract_summary_full',
                'value_report_contract_summary_full',
            ]),
        ])
        self.values_obj.unlink(self.cursor, self.uid, [combined_value.id])
        self.report_obj.unlink(self.cursor, self.uid, [combined_action.id])
        self.imd_obj.unlink(self.cursor, self.uid, combined_imd_ids)

        migration = self._load_migration()
        migration.up(self.cursor, '5.0.25.7')
        migration.up(self.cursor, '5.0.25.7')

        self._assert_summary_print_route()
        self._assert_combined_print_route()
        self.assertEqual(
            self.report_obj.read(
                self.cursor, self.uid, summary_action.id, ['name', 'report_name']
            ),
            summary_action_data
        )
        self.assertEqual(
            self.values_obj.read(
                self.cursor, self.uid, summary_value.id,
                ['model', 'name', 'value']
            ),
            summary_value_data
        )

    def _load_migration(self):
        migration_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'migrations',
            '5.0.25.8',
            'post-0001_update_contract_summary_report.py'
        ))
        return imp.load_source(
            'contract_summary_full_report_migration', migration_path
        )

    def _assert_summary_print_route(self):
        self._assert_print_route(
            'report_contract_summary',
            'value_report_contract_summary',
            'giscedata.polissa.contract.summary',
            'Contract Summary'
        )

    def _assert_combined_print_route(self):
        self._assert_print_route(
            'report_contract_summary_full',
            'value_report_contract_summary_full',
            'giscedata.polissa.contract.summary.full',
            'Contract Summary and Conditions'
        )

    def _assert_print_route(self, report_ref, value_ref, report_name, display_name):
        report_action = self.imd_obj._get_obj(
            self.cursor,
            self.uid,
            'som_polissa_condicions_generals',
            report_ref
        )
        print_value = self.imd_obj._get_obj(
            self.cursor,
            self.uid,
            'som_polissa_condicions_generals',
            value_ref
        )
        report_data = self.report_obj.read(
            self.cursor, self.uid, report_action.id, ['name', 'report_name']
        )
        value_data = self.values_obj.read(
            self.cursor, self.uid, print_value.id, ['model', 'name', 'value']
        )

        self.assertEqual(
            report_data['report_name'],
            report_name
        )
        self.assertEqual(report_data['name'], display_name)
        self.assertEqual(value_data['model'], 'giscedata.polissa')
        self.assertEqual(
            value_data['name'],
            report_name
        )
        self.assertEqual(
            value_data['value'],
            'ir.actions.report.xml,{0}'.format(report_action.id)
        )
