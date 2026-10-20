# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64
import json
import os
import tempfile
import unittest

import mock

from som_holder_change.models import holder_change_reports


class TestHolderChangeReports(unittest.TestCase):

    def setUp(self):
        sudo = mock.patch.object(holder_change_reports, "Sudo")
        sudo.start()
        self.addCleanup(sudo.stop)

    def snapshot(self):
        return {
            "version": 1,
            "card_placeholder": "unique-card-placeholder",
            "documents": [
                {"html": "<html>Resum de Júlia: unique-card-placeholder; preu 0.0000</html>",
                 "appended_pdfs": []},
                {"html": "<html>Contracte: unique-card-placeholder</html>",
                 "appended_pdfs": []},
            ],
        }

    def test_prepare_snapshot_freezes_html_and_appended_pdfs(self):
        pool = mock.Mock()
        pool.get.return_value.read.return_value = {"groups_id": [1]}
        pool.get.return_value.get_pdfs_to_append.return_value = [b"%PDF-annex"]
        caller_context = {"lang": "ca_ES"}

        def create_html(cursor, uid, ids, data, report_values, context=None):
            self.assertEqual(report_values["report_type"], "pdf")
            return "<html>Júlia: {}</html>".format(
                context[holder_change_reports.CARD_PLACEHOLDER_CONTEXT]
            ).encode("utf-8")

        with mock.patch.object(holder_change_reports.netsvc, "LocalService") as service:
            service.return_value._service.get_report_v.return_value = {"id": 1, "context": {}}
            service.return_value._service.create_html.side_effect = create_html
            snapshot = holder_change_reports.prepare_snapshot(
                mock.Mock(), 1, pool, 42, context=caller_context
            )

        self.assertEqual(json.loads(json.dumps(snapshot)), snapshot)
        self.assertEqual(caller_context, {"lang": "ca_ES"})
        self.assertEqual(service.call_count, 2)
        service.return_value.create.assert_not_called()
        append_context = pool.get.return_value.get_pdfs_to_append.call_args[1]["context"]
        self.assertNotIn("report_type", append_context)
        self.assertNotIn(holder_change_reports.CARD_PLACEHOLDER_CONTEXT, append_context)
        for document in snapshot["documents"]:
            self.assertIn(snapshot["card_placeholder"], document["html"])
            self.assertIn("Júlia", document["html"])
            self.assertEqual(base64.b64decode(document["appended_pdfs"][0]), b"%PDF-annex")

    def test_prepare_snapshot_rejects_reports_without_placeholder(self):
        pool = mock.Mock()
        pool.get.return_value.read.return_value = {"groups_id": [1]}
        with mock.patch.object(holder_change_reports.netsvc, "LocalService") as service:
            service.return_value._service.get_report_v.return_value = {"id": 1, "context": {}}
            service.return_value._service.create_html.return_value = "<html>Error</html>"
            with self.assertRaises(ValueError):
                holder_change_reports.prepare_snapshot(mock.Mock(), 1, pool, 42)

    def test_prepare_snapshot_propagates_template_errors_before_payment(self):
        pool = mock.Mock()
        pool.get.return_value.read.return_value = {"groups_id": [1]}
        with mock.patch.object(holder_change_reports.netsvc, "LocalService") as service:
            service.return_value._service.get_report_v.return_value = {"id": 1, "context": {}}
            service.return_value._service.create_html.side_effect = ValueError("Invalid template")
            with self.assertRaises(ValueError):
                holder_change_reports.prepare_snapshot(mock.Mock(), 1, pool, 42)
        service.return_value.create.assert_not_called()
        pool.get.return_value.get_pdfs_to_append.assert_not_called()

    def test_render_uses_only_snapshot_and_replaces_only_card_placeholder(self):
        snapshot = self.snapshot()
        original = json.loads(json.dumps(snapshot))
        temporary_paths = []

        def temporary_pdf():
            descriptor, path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(descriptor, "wb") as pdf_file:
                pdf_file.write(b"%PDF-document")
            temporary_paths.append(path)
            return path

        def render(html, params=None, context=None):
            html = html.decode("utf-8")
            self.assertIn("1234", html)
            self.assertNotIn(snapshot["card_placeholder"], html)
            return temporary_pdf()

        with mock.patch.object(
            holder_change_reports.PuppeteerParser, "render", side_effect=render
        ) as renderer:
            with mock.patch.object(
                holder_change_reports.pypdftk, "concat", side_effect=lambda files: temporary_pdf()
            ):
                reports = holder_change_reports.render_snapshot(snapshot, "**** **** **** 1234")

        self.assertEqual(base64.b64decode(reports["contract_pdf"]), b"%PDF-document")
        self.assertFalse(reports["mandate_pdf"])
        self.assertEqual(renderer.call_count, 2)
        self.assertIn("preu 0.0000", renderer.call_args_list[0][0][0].decode("utf-8"))
        self.assertIn("Júlia", renderer.call_args_list[0][0][0].decode("utf-8"))
        self.assertEqual(snapshot, original)
        self.assertTrue(all(not os.path.exists(path) for path in temporary_paths))

    def test_render_cleans_temporary_files_when_second_document_fails(self):
        descriptor, path = tempfile.mkstemp(suffix=".pdf")
        os.close(descriptor)
        with mock.patch.object(
            holder_change_reports.PuppeteerParser, "render",
            side_effect=[path, Exception("Renderer failed")],
        ):
            with self.assertRaises(Exception):
                holder_change_reports.render_snapshot(self.snapshot(), "**** 1234")
        self.assertFalse(os.path.exists(path))

    def test_render_preserves_appended_pdfs_in_document_order(self):
        snapshot = self.snapshot()
        snapshot["documents"][0]["appended_pdfs"] = [
            base64.b64encode(b"%PDF-annex").decode("ascii")
        ]
        paths = []

        def temporary_pdf(content):
            descriptor, path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(descriptor, "wb") as pdf_file:
                pdf_file.write(content)
            paths.append(path)
            return path

        def concat(files):
            contents = []
            for path in files:
                with open(path, "rb") as pdf_file:
                    contents.append(pdf_file.read())
            self.assertEqual(contents, [b"%PDF-summary", b"%PDF-annex", b"%PDF-contract"])
            return temporary_pdf(b"%PDF-merged")

        with mock.patch.object(
            holder_change_reports.PuppeteerParser, "render",
            side_effect=[temporary_pdf(b"%PDF-summary"), temporary_pdf(b"%PDF-contract")],
        ):
            with mock.patch.object(
                holder_change_reports.PuppeteerParser, "write_temporal_file",
                side_effect=lambda content, extension: temporary_pdf(content),
            ):
                with mock.patch.object(holder_change_reports.pypdftk, "concat", side_effect=concat):
                    result = holder_change_reports.render_snapshot(snapshot, "**** 1234")
        self.assertEqual(base64.b64decode(result["contract_pdf"]), b"%PDF-merged")
        self.assertTrue(all(not os.path.exists(path) for path in paths))

    def test_render_rejects_missing_snapshot_or_incomplete_card(self):
        for snapshot, card in ((False, "**** 1234"), (self.snapshot(), "***")):
            with self.assertRaises(ValueError):
                holder_change_reports.render_snapshot(snapshot, card)
