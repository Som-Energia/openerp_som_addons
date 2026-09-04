# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
from datetime import datetime, timedelta
from destral import testing
from osv import osv
import mock
from .. import refund_rectify_batch
from giscedata_polissa import giscedata_cups


class TestWizardRefundRectifyBatch(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestWizardRefundRectifyBatch, self).setUp()
        self.pool = self.openerp.pool
        self.wizard_obj = self.pool.get("wizard.refund.rectify.batch")
        self.f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        self.imd_obj = self.pool.get("ir.model.data")

    def _f1_id(self, xml_id):
        return self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", xml_id
        )[1]

    def _same_polissa_f1s(self):
        first_id = self._f1_id("line_01_f1_import_01")
        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        polissa = self.pool.get("giscedata.polissa").browse(
            self.cursor, self.uid, polissa_id
        )
        initial_date = polissa.data_alta
        final_date = (datetime.strptime(initial_date, "%Y-%m-%d") + timedelta(days=27)).strftime(
            "%Y-%m-%d"
        )
        second_initial_date = (
            datetime.strptime(final_date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        second_final_date = (
            datetime.strptime(second_initial_date, "%Y-%m-%d") + timedelta(days=27)
        ).strftime("%Y-%m-%d")
        self.f1_obj.write(
            self.cursor,
            self.uid,
            first_id,
            {
                "state": "valid",
                "cups_id": polissa.cups.id,
                "cups_text": polissa.cups.name,
                "fecha_factura_desde": initial_date,
                "fecha_factura_hasta": final_date,
                "type_factura": "R",
            },
        )
        second_id = self.f1_obj.copy(
            self.cursor,
            self.uid,
            first_id,
            {
                "fecha_factura_desde": second_initial_date,
                "fecha_factura_hasta": second_final_date,
            },
        )
        return first_id, second_id

    def test_create_batch_rejects_empty_selection(self):
        wizard_id = self.wizard_obj.create(self.cursor, self.uid, {}, context={})

        self.assertRaises(
            osv.except_osv,
            self.wizard_obj.create_batch,
            self.cursor,
            self.uid,
            [wizard_id],
            context={},
        )

    def test_create_batch_creates_ordered_lines_for_one_polissa(self):
        first_id, second_id = self._same_polissa_f1s()
        context = {"active_ids": [second_id, first_id]}
        wizard_id = self.wizard_obj.create(self.cursor, self.uid, {}, context=context)

        batch_obj = self.pool.get("refund.rectify.batch")
        with mock.patch.object(batch_obj, "schedule_batch_execution"):
            action = self.wizard_obj.create_batch(
                self.cursor, self.uid, [wizard_id], context=context
            )
        batch = self.pool.get("refund.rectify.batch").browse(
            self.cursor, self.uid, action["res_id"]
        )

        self.assertEqual(batch.state, "pending")
        self.assertEqual([line.f1_id.id for line in batch.line_ids], [first_id, second_id])
        self.assertEqual([line.sequence for line in batch.line_ids], [1, 2])

    def test_create_batch_rejects_multiple_policies(self):
        first_id = self._f1_id("line_01_f1_import_01")
        second_id = self._f1_id("line_02_f1_import_01")
        self.f1_obj.write(
            self.cursor, self.uid, [first_id, second_id], {"type_factura": "R"}
        )
        context = {"active_ids": [first_id, second_id]}
        wizard_id = self.wizard_obj.create(self.cursor, self.uid, {}, context=context)

        self.assertRaises(
            osv.except_osv,
            self.wizard_obj.create_batch,
            self.cursor,
            self.uid,
            [wizard_id],
            context=context,
        )


class TestRefundRectifyBatchCreation(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRefundRectifyBatchCreation, self).setUp()
        self.pool = self.openerp.pool
        self.batch_obj = self.pool.get("refund.rectify.batch")

    def _f1(self, f1_id, polissa_id=7, **values):
        cups = mock.Mock()
        cups.id = 13
        f1 = mock.Mock()
        f1.id = f1_id
        f1.type_factura = "R"
        f1.fecha_factura_desde = "2022-01-01"
        f1.fecha_factura_hasta = "2022-01-31"
        f1.cups_id = cups
        if polissa_id:
            polissa = mock.Mock()
            polissa.id = polissa_id
            polissa.name = "POL-%s" % polissa_id
            f1.polissa_id = polissa
        else:
            f1.polissa_id = False
        for field, value in values.items():
            setattr(f1, field, value)
        return f1

    def _assert_create_batch_rejected(self, f1s):
        f1_obj = mock.Mock()
        line_obj = mock.Mock()
        f1_obj.search.return_value = [f1.id for f1 in f1s]
        f1_obj.browse.return_value = f1s
        with mock.patch.object(
                self.pool,
                "get",
                side_effect=lambda model: {
                    "giscedata.facturacio.importacio.linia": f1_obj,
                    "refund.rectify.batch.line": line_obj,
                }[model]):
            with mock.patch.object(self.batch_obj, "create", return_value=12):
                try:
                    self.batch_obj.create_batch(
                        self.cursor,
                        self.uid,
                        [f1.id for f1 in f1s],
                        context={},
                    )
                except osv.except_osv as error:
                    return error
        self.fail("Expected batch creation to be rejected")

    def test_create_batch_rejects_empty_selection_without_wizard(self):
        self._assert_create_batch_rejected([])

    def test_create_batch_rejects_invalid_f1_data_without_wizard(self):
        invalid_f1s = [
            self._f1(1, type_factura="C"),
            self._f1(2, fecha_factura_desde=False),
            self._f1(3, fecha_factura_hasta="not-a-date"),
            self._f1(
                4,
                fecha_factura_desde="2022-02-01",
                fecha_factura_hasta="2022-01-31",
            ),
            self._f1(5, cups_id=False),
            self._f1(6, polissa_id=False),
        ]
        for f1 in invalid_f1s:
            self._assert_create_batch_rejected([f1])

    def test_create_batch_rejects_f1s_resolved_to_multiple_policies(self):
        error = self._assert_create_batch_rejected([
            self._f1(1, polissa_id=7), self._f1(2, polissa_id=9),
        ])
        self.assertTrue("POL-7" in error.value)
        self.assertTrue("POL-9" in error.value)

    def test_create_batch_rejects_existing_active_batch(self):
        f1 = self._f1(1)
        f1_obj = mock.Mock()
        f1_obj.search.return_value = [f1.id]
        f1_obj.browse.return_value = [f1]
        line_obj = mock.Mock()
        cursor = mock.Mock()
        with mock.patch.object(
                self.pool,
                "get",
                side_effect=lambda model: {
                    "giscedata.facturacio.importacio.linia": f1_obj,
                    "refund.rectify.batch.line": line_obj,
                }[model]):
            with mock.patch.object(self.batch_obj, "search", return_value=[12]) as search:
                self.assertRaises(
                    osv.except_osv,
                    self.batch_obj.create_batch,
                    cursor,
                    self.uid,
                    [f1.id],
                    context={},
                )

        search.assert_called_once_with(
            cursor,
            self.uid,
            [("polissa_id", "=", 7), ("state", "in", ["pending", "running", "blocked"])],
            context={},
        )

    def test_create_batch_creates_chronological_lines_without_policy_lock(self):
        first_f1 = self._f1(1)
        second_f1 = self._f1(2)
        f1_obj = mock.Mock()
        f1_obj.search.return_value = [first_f1.id, second_f1.id]
        f1_obj.browse.return_value = [second_f1, first_f1]
        line_obj = mock.Mock()
        cursor = mock.Mock()
        with mock.patch.object(
                self.pool,
                "get",
                side_effect=lambda model: {
                    "giscedata.facturacio.importacio.linia": f1_obj,
                    "refund.rectify.batch.line": line_obj,
                }[model]):
            with mock.patch.object(self.batch_obj, "search", return_value=[]):
                with mock.patch.object(self.batch_obj, "create", return_value=12):
                    batch_id = self.batch_obj.create_batch(
                        cursor, self.uid, [second_f1.id, first_f1.id], context={}
                    )

        self.assertEqual(batch_id, 12)
        self.assertEqual(cursor.execute.call_count, 0)
        self.assertEqual(
            [call[0][2] for call in line_obj.create.call_args_list],
            [
                {"batch_id": 12, "f1_id": first_f1.id, "sequence": 1},
                {"batch_id": 12, "f1_id": second_f1.id, "sequence": 2},
            ],
        )


class TestRefundRectifyBatchScheduling(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRefundRectifyBatchScheduling, self).setUp()
        self.pool = self.openerp.pool
        self.batch_obj = self.pool.get("refund.rectify.batch")
        self.wizard_obj = self.pool.get("wizard.refund.rectify.batch")

    def test_schedules_one_primitive_batch_job_and_defers_worker_to_commit(self):
        cursor = mock.Mock()
        queued_job = mock.Mock()
        queued_job.id = "rq-job-12"
        context = {"active_ids": [3, 4]}
        with mock.patch.object(
                self.batch_obj,
                "process_batch_f1_lines_async",
                return_value=queued_job) as async_job:
            with mock.patch.object(refund_rectify_batch, "AutoWorker") as worker_class:
                worker = worker_class.return_value
                with mock.patch.object(self.batch_obj, "write") as write:
                    self.batch_obj.schedule_batch_execution(
                        cursor, self.uid, 12, context=context
                    )

        async_job.assert_called_once_with(cursor, self.uid, 12)
        write.assert_called_once_with(
            cursor, self.uid, [12], {"job_reference": "rq-job-12"}, context=context
        )
        worker_class.assert_called_once_with(
            queue="refund_rectify_f1", default_result_ttl=24 * 3600, max_procs=1
        )
        worker.work.assert_called_once_with(cursor)

    def test_wizard_returns_batch_form_after_requesting_schedule(self):
        batch_obj = mock.Mock()
        batch_obj.create_batch.return_value = 12
        context = {"active_ids": [3, 4]}
        with mock.patch.object(self.pool, "get", return_value=batch_obj):
            action = self.wizard_obj.create_batch(
                self.cursor, self.uid, [1], context=context
            )

        batch_obj.create_batch.assert_called_once_with(
            self.cursor, self.uid, [3, 4], context=context
        )
        batch_obj.schedule_batch_execution.assert_called_once_with(
            self.cursor, self.uid, 12, context=context
        )
        self.assertEqual(action, {
            "type": "ir.actions.act_window",
            "name": "Lot pendent d'abonar i rectificar",
            "res_model": "refund.rectify.batch",
            "view_type": "form",
            "view_mode": "form",
            "res_id": 12,
            "target": "current",
        })


class TestRefundRectifyBatchLineProcessOneF1(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRefundRectifyBatchLineProcessOneF1, self).setUp()
        self.pool = self.openerp.pool
        self.line_obj = self.pool.get("refund.rectify.batch.line")
        self.f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        self.fact_obj = self.pool.get("giscedata.facturacio.factura")
        self.imd_obj = self.pool.get("ir.model.data")

    def _prepare_rectifying_f1(self):
        fact_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "factura_0003"
        )[1]
        f1_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_switching", "line_01_f1_import_01"
        )[1]
        fact_info = self.fact_obj.read(
            self.cursor, self.uid, fact_id,
            ["origin", "polissa_id", "data_inici", "data_final", "cups_id"]
        )
        self.f1_obj.write(
            self.cursor, self.uid, [f1_id], {
                "invoice_number_text": fact_info["origin"],
                "cups_id": fact_info["cups_id"][0],
                "fecha_factura_desde": fact_info["data_inici"],
                "fecha_factura_hasta": fact_info["data_final"],
                "type_factura": "R",
            }
        )
        fact_info["polissa_id"] = self.f1_obj.read(
            self.cursor, self.uid, f1_id, ["polissa_id"]
        )["polissa_id"]
        return f1_id, fact_info

    def _patch_most_recent_polissa(self, fact_info):
        return mock.patch.object(
            giscedata_cups.GiscedataCupsPs,
            "find_most_recent_polissa",
            return_value={fact_info["cups_id"][0]: fact_info["polissa_id"][0]},
        )

    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_write_f1_observation")
    @mock.patch.object(
        refund_rectify_batch.RefundRectifyBatchLine, "_delete_draft_invoices_if_needed"
    )
    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_refund_rectify_if_needed")
    @mock.patch.object(
        refund_rectify_batch.RefundRectifyBatchLine, "_recarregar_lectures_between_dates"
    )
    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_get_factures_client_by_dates")
    def test_process_one_f1_returns_generated_ids_after_cleanup(
            self, mock_invoices, mock_readings, mock_refund, mock_cleanup,
            mock_observation):
        f1_id, fact_info = self._prepare_rectifying_f1()
        polissa_id = fact_info["polissa_id"][0]
        with self._patch_most_recent_polissa(fact_info):
            call_order = []
            mock_invoices.side_effect = lambda *args, **kwargs: (
                call_order.append("invoices")
                or ([31], "S'han eliminat 1 factures en esborrany", [])
            )
            mock_readings.side_effect = lambda *args, **kwargs: call_order.append("readings") or 2
            mock_refund.side_effect = (
                lambda *args, **kwargs: call_order.append("refund") or [41, 42, 43]
            )
            mock_cleanup.side_effect = lambda *args, **kwargs: (
                call_order.append("cleanup")
                or (["Les factures AB i RE tenen import diferent."], [42, 43])
            )
            mock_observation.side_effect = lambda *args, **kwargs: call_order.append("observation")
            with mock.patch.object(
                    self.line_obj, "_get_f1_meter_ids", return_value=[1]):
                result = self.line_obj.process_one_f1(
                    self.cursor, self.uid, f1_id, expected_polissa_id=polissa_id, context={}
                )

        self.assertEqual(result["status"], "processed")
        self.assertEqual(result["source_invoice_ids"], [31])
        self.assertEqual(result["removed_draft_invoice_ids"], [])
        self.assertEqual(result["reloaded_reading_count"], 2)
        self.assertEqual(result["generated_invoice_ids"], [42, 43])
        self.assertTrue(result["observation_written"])
        self.assertEqual(call_order, ["invoices", "readings", "refund", "cleanup", "observation"])
        mock_refund.assert_called_once_with(
            self.cursor, self.uid, [31], context={}
        )
        mock_cleanup.assert_called_once_with(
            self.cursor, self.uid, [41, 42, 43], [31], context={}
        )

    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_write_f1_observation")
    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_get_factures_client_by_dates")
    def test_process_one_f1_preserves_draft_cleanup_before_no_action(
            self, mock_invoices, mock_observation):
        f1_id, fact_info = self._prepare_rectifying_f1()
        with self._patch_most_recent_polissa(fact_info):
            mock_invoices.return_value = ([], "S'han eliminat 1 factures en esborrany", [51])
            with mock.patch.object(
                    self.line_obj, "_get_f1_meter_ids", return_value=[1]):
                result = self.line_obj.process_one_f1(self.cursor, self.uid, f1_id, context={})

        self.assertEqual(result["status"], "no_action")
        self.assertEqual(result["removed_draft_invoice_ids"], [51])
        self.assertEqual(result["generated_invoice_ids"], [])
        self.assertTrue(result["observation_written"])
        mock_observation.assert_called_once()

    def test_process_one_f1_rejects_expected_polissa_mismatch(self):
        f1_id, fact_info = self._prepare_rectifying_f1()
        polissa_id = fact_info["polissa_id"][0]
        with self._patch_most_recent_polissa(fact_info):
            self.assertRaises(
                osv.except_osv,
                self.line_obj.process_one_f1,
                self.cursor,
                self.uid,
                f1_id,
                expected_polissa_id=polissa_id + 1,
                context={},
            )

    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_refund_rectify_if_needed")
    def test_process_one_f1_returns_no_action_for_non_rectifying_f1(
            self, mock_refund):
        f1_id, fact_info = self._prepare_rectifying_f1()
        self.f1_obj.write(self.cursor, self.uid, f1_id, {"type_factura": "C"})
        with self._patch_most_recent_polissa(fact_info):
            with mock.patch.object(
                    self.line_obj, "_get_f1_meter_ids", return_value=[1]):
                result = self.line_obj.process_one_f1(self.cursor, self.uid, f1_id, context={})

        self.assertEqual(result["status"], "no_action")
        self.assertFalse(result["observation_written"])
        self.assertFalse(mock_refund.called)

    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_refund_rectify_if_needed")
    def test_process_one_f1_returns_no_action_for_suspended_polissa(
            self, mock_refund):
        f1_id, fact_info = self._prepare_rectifying_f1()
        polissa_id = fact_info["polissa_id"][0]
        self.pool.get("giscedata.polissa").write(
            self.cursor, self.uid, polissa_id, {"facturacio_suspesa": True}
        )
        with self._patch_most_recent_polissa(fact_info):
            with mock.patch.object(
                    self.line_obj, "_get_f1_meter_ids", return_value=[1]):
                result = self.line_obj.process_one_f1(self.cursor, self.uid, f1_id, context={})

        self.assertEqual(result["status"], "no_action")
        self.assertFalse(result["observation_written"])
        self.assertFalse(mock_refund.called)

    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_refund_rectify_if_needed")
    @mock.patch.object(
        refund_rectify_batch.RefundRectifyBatchLine, "_recarregar_lectures_between_dates"
    )
    @mock.patch.object(refund_rectify_batch.RefundRectifyBatchLine, "_get_factures_client_by_dates")
    def test_process_one_f1_returns_no_action_without_readings(
            self, mock_invoices, mock_readings, mock_refund):
        f1_id, fact_info = self._prepare_rectifying_f1()
        with self._patch_most_recent_polissa(fact_info):
            mock_invoices.return_value = ([31], "", [])
            mock_readings.return_value = 0
            with mock.patch.object(
                    self.line_obj, "_get_f1_meter_ids", return_value=[1]):
                result = self.line_obj.process_one_f1(self.cursor, self.uid, f1_id, context={})

        self.assertEqual(result["status"], "no_action")
        self.assertFalse(result["observation_written"])
        self.assertFalse(mock_refund.called)

    def test_process_one_f1_never_owns_transactions(self):
        polissa = mock.Mock()
        polissa.id = 7
        polissa.name = "0123456"
        polissa.facturacio_suspesa = False
        f1 = mock.Mock()
        f1.id = 9
        f1.polissa_id = polissa
        f1.invoice_number_text = "ESDFER0123456789B"
        f1.type_factura = "R"
        f1.fecha_factura_desde = "2022-01-01"
        f1.fecha_factura_hasta = "2022-01-31"
        f1_obj = mock.Mock()
        f1_obj.search.return_value = [f1.id]
        f1_obj.browse.return_value = f1
        cursor = mock.Mock()

        with mock.patch.object(self.pool, "get", return_value=f1_obj):
            with mock.patch.object(self.line_obj, "_get_f1_meter_ids", return_value=[1]):
                with mock.patch.object(
                        self.line_obj,
                        "_get_factures_client_by_dates",
                        return_value=([10], "", [])):
                    with mock.patch.object(
                            self.line_obj, "_recarregar_lectures_between_dates", return_value=1):
                        with mock.patch.object(
                                self.line_obj, "_refund_rectify_if_needed", return_value=[20]):
                            with mock.patch.object(
                                    self.line_obj,
                                    "_delete_draft_invoices_if_needed",
                                    return_value=([], [20])):
                                with mock.patch.object(
                                        self.line_obj, "_write_refacturation_observation"):
                                    result = self.line_obj.process_one_f1(
                                        cursor, self.uid, f1.id, context={}
                                    )

        self.assertEqual(result["generated_invoice_ids"], [20])
        self.assertFalse(cursor.commit.called)
        self.assertFalse(cursor.rollback.called)


class TestRefundRectifyBatchLineReadingAnchors(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRefundRectifyBatchLineReadingAnchors, self).setUp()
        self.pool = self.openerp.pool
        self.line_obj = self.pool.get("refund.rectify.batch.line")

    def _f1(self, serials, polissa_id=7):
        f1 = mock.Mock()
        f1.polissa_id.id = polissa_id
        f1.importacio_lectures_ids = []
        for serial in serials:
            lectura = mock.Mock()
            lectura.comptador = serial
            f1.importacio_lectures_ids.append(lectura)
        return f1

    def test_resolves_only_f1_meters_including_inactive_ones(self):
        meter_obj = mock.Mock()
        meter_obj.search.return_value = [3, 9]
        meter_a = mock.Mock()
        meter_a.id = 3
        meter_a.name = "METER-A"
        meter_b = mock.Mock()
        meter_b.id = 9
        meter_b.name = "METER-B"
        meter_obj.browse.return_value = [meter_a, meter_b]
        with mock.patch.object(self.pool, "get", return_value=meter_obj):
            meter_ids = self.line_obj._get_f1_meter_ids(
                self.cursor, self.uid, self._f1(["METER-B", "METER-A"]), context={}
            )

        self.assertEqual(meter_ids, [3, 9])
        domain = meter_obj.search.call_args[0][2]
        self.assertEqual(domain, [("polissa", "=", 7), ("name", "in", ["METER-A", "METER-B"])])
        self.assertFalse(meter_obj.search.call_args[1]["context"]["active_test"])

    def test_rejects_missing_or_ambiguous_f1_meter_serials(self):
        meter_obj = mock.Mock()
        meter_obj.search.return_value = [3, 9]
        meter_a = mock.Mock()
        meter_a.id = 3
        meter_a.name = "METER-A"
        duplicate_meter_a = mock.Mock()
        duplicate_meter_a.id = 9
        duplicate_meter_a.name = "METER-A"
        meter_obj.browse.return_value = [meter_a, duplicate_meter_a]
        with mock.patch.object(self.pool, "get", return_value=meter_obj):
            self.assertRaises(
                osv.except_osv,
                self.line_obj._get_f1_meter_ids,
                self.cursor,
                self.uid,
                self._f1(["METER-A", "METER-B"]),
                context={},
            )

    def test_rejects_f1_without_meter_serials(self):
        self.assertRaises(
            osv.except_osv,
            self.line_obj._get_f1_meter_ids,
            self.cursor,
            self.uid,
            self._f1([]),
            context={},
        )

    def test_rejects_meter_mapping_before_invoice_lookup(self):
        polissa = mock.Mock()
        polissa.id = 7
        polissa.facturacio_suspesa = False
        f1 = self._f1(["METER-A"])
        f1.id = 9
        f1.polissa_id = polissa
        f1.invoice_number_text = "ESDFE987654321A"
        f1.type_factura = "R"
        f1.fecha_factura_desde = "2022-01-01"
        f1.fecha_factura_hasta = "2022-01-31"
        f1_obj = mock.Mock()
        f1_obj.search.return_value = [f1.id]
        f1_obj.browse.return_value = f1
        with mock.patch.object(self.pool, "get", return_value=f1_obj):
            with mock.patch.object(
                    self.line_obj,
                    "_get_f1_meter_ids",
                    side_effect=osv.except_osv("Error", "Sense comptador")):
                with mock.patch.object(self.line_obj, "_get_factures_client_by_dates") as invoices:
                    self.assertRaises(
                        osv.except_osv,
                        self.line_obj.process_one_f1,
                        self.cursor,
                        self.uid,
                        f1.id,
                        context={},
                    )
        self.assertFalse(invoices.called)

    def test_builds_anchors_for_every_f1_meter_with_initial_date_priority(self):
        lectura_pool_obj = mock.Mock()
        lectura_pool_obj.search.side_effect = [[101], [102], [201], [202]]
        with mock.patch.object(self.pool, "get", return_value=lectura_pool_obj):
            anchors = self.line_obj._get_reading_anchor_ids(
                self.cursor, self.uid, [1, 2], "2022-02-01", "2022-02-28", context={}
            )

        self.assertEqual(anchors, [101, 102, 201, 202])
        self.assertEqual(
            lectura_pool_obj.search.call_args_list[0][0][2],
            [("comptador", "=", 1), ("name", "=", "2022-02-01")],
        )
        self.assertEqual(
            lectura_pool_obj.search.call_args_list[2][0][2],
            [("comptador", "=", 2), ("name", "=", "2022-02-01")],
        )

    def test_uses_previous_day_only_when_initial_anchor_is_missing(self):
        lectura_pool_obj = mock.Mock()
        lectura_pool_obj.search.side_effect = [[], [201], [202]]
        with mock.patch.object(self.pool, "get", return_value=lectura_pool_obj):
            anchors = self.line_obj._get_reading_anchor_ids(
                self.cursor, self.uid, [2], "2022-02-01", "2022-02-28", context={}
            )

        self.assertEqual(anchors, [201, 202])
        self.assertEqual(
            lectura_pool_obj.search.call_args_list[1][0][2],
            [("comptador", "=", 2), ("name", "=", "2022-01-31")],
        )

    def test_deduplicates_identical_meter_date_anchors(self):
        lectura_pool_obj = mock.Mock()
        lectura_pool_obj.search.side_effect = [[101], [102]]
        with mock.patch.object(self.pool, "get", return_value=lectura_pool_obj):
            anchors = self.line_obj._get_reading_anchor_ids(
                self.cursor, self.uid, [1], "2022-02-01", "2022-02-01", context={}
            )

        self.assertEqual(anchors, [101])

    def test_omits_initial_anchor_when_requested(self):
        lectura_pool_obj = mock.Mock()
        lectura_pool_obj.search.return_value = [102]
        with mock.patch.object(self.pool, "get", return_value=lectura_pool_obj):
            anchors = self.line_obj._get_reading_anchor_ids(
                self.cursor, self.uid, [1], "2022-02-01", "2022-02-28",
                reload_initial=False, context={}
            )

        self.assertEqual(anchors, [102])
        self.assertEqual(lectura_pool_obj.search.call_count, 1)
        self.assertEqual(
            lectura_pool_obj.search.call_args[0][2],
            [("comptador", "=", 1), ("name", "=", "2022-02-28")],
        )


class TestRefundRectifyBatchLineSequentialReadingPlan(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRefundRectifyBatchLineSequentialReadingPlan, self).setUp()
        self.pool = self.openerp.pool
        self.line_obj = self.pool.get("refund.rectify.batch.line")
        self.batch_obj = self.pool.get("refund.rectify.batch")

    def _f1(self, initial, final):
        f1 = mock.Mock()
        f1.fecha_factura_desde = initial
        f1.fecha_factura_hasta = final
        return f1

    def test_omits_initial_only_after_continuous_same_meter_predecessor(self):
        previous_f1 = self._f1("2022-01-01", "2022-01-31")
        current_f1 = self._f1("2022-02-01", "2022-02-28")
        f1_obj = mock.Mock()
        f1_obj.browse.return_value = previous_f1
        with mock.patch.object(self.pool, "get", return_value=f1_obj):
            with mock.patch.object(self.line_obj, "_get_f1_meter_ids", return_value=[7]):
                plan = self.line_obj._build_reading_anchor_plan(
                    self.cursor, self.uid, current_f1, [7], previous_f1_id=10,
                    predecessor_processed=True, context={}
                )

        self.assertEqual(plan, {"meter_ids": [7], "reload_initial": False})

    def test_reloads_both_anchors_after_gap_meter_change_or_no_action(self):
        previous_f1 = self._f1("2022-01-01", "2022-01-30")
        current_f1 = self._f1("2022-02-01", "2022-02-28")
        f1_obj = mock.Mock()
        f1_obj.browse.return_value = previous_f1
        with mock.patch.object(self.pool, "get", return_value=f1_obj):
            with mock.patch.object(self.line_obj, "_get_f1_meter_ids", return_value=[8]):
                gap_plan = self.line_obj._build_reading_anchor_plan(
                    self.cursor, self.uid, current_f1, [7], previous_f1_id=10,
                    predecessor_processed=True, context={}
                )
                no_action_plan = self.line_obj._build_reading_anchor_plan(
                    self.cursor, self.uid, current_f1, [7], previous_f1_id=10,
                    predecessor_processed=False, context={}
                )

        self.assertTrue(gap_plan["reload_initial"])
        self.assertTrue(no_action_plan["reload_initial"])

    def test_processes_batch_lines_in_order_with_predecessor_outcome(self):
        batch = mock.Mock()
        batch.polissa_id.id = 7
        first_line = mock.Mock()
        first_line.f1_id.id = 11
        second_line = mock.Mock()
        second_line.f1_id.id = 12
        batch.line_ids = [first_line, second_line]
        line_obj = mock.Mock()
        line_obj.process_one_f1.side_effect = [
            {"status": "processed"}, {"status": "no_action"}
        ]
        with mock.patch.object(self.pool, "get", return_value=line_obj):
            with mock.patch.object(self.batch_obj, "browse", return_value=batch):
                with mock.patch.object(self.batch_obj, "write"):
                    with mock.patch.object(line_obj, "_mark_line_running"):
                        with mock.patch.object(line_obj, "_persist_line_outcome"):
                            results = self.batch_obj.process_batch_f1_lines(
                                self.cursor, self.uid, 3, context={}
                            )

        self.assertEqual(results, [{"status": "processed"}, {"status": "no_action"}])
        self.assertEqual(
            line_obj.process_one_f1.call_args_list,
            [
                mock.call(
                    self.cursor, self.uid, 11, expected_polissa_id=7,
                    previous_f1_id=None, predecessor_processed=False, context={}
                ),
                mock.call(
                    self.cursor, self.uid, 12, expected_polissa_id=7,
                    previous_f1_id=11, predecessor_processed=True, context={}
                ),
            ],
        )


class TestRefundRectifyBatchExecutionPersistence(testing.OOTestCaseWithCursor):
    def setUp(self):
        super(TestRefundRectifyBatchExecutionPersistence, self).setUp()
        self.pool = self.openerp.pool
        self.line_obj = self.pool.get("refund.rectify.batch.line")
        self.batch_obj = self.pool.get("refund.rectify.batch")

    def test_persists_functional_line_outcome_and_refreshes_batch(self):
        batch_obj = mock.Mock()
        result = {
            "status": "processed",
            "messages": ["F1 processat"],
            "generated_invoice_ids": [31, 32],
        }

        with mock.patch.object(self.pool, "get", return_value=batch_obj):
            with mock.patch.object(
                    self.line_obj, "read", return_value={"batch_id": [7, "F1_R-TASCA-7"]}):
                with mock.patch.object(self.line_obj, "write") as write:
                    self.line_obj._persist_line_outcome(
                        self.cursor, self.uid, 3, result=result, context={}
                    )

        vals = write.call_args[0][3]
        self.assertEqual(vals["state"], "done")
        self.assertEqual(vals["outcome"], "processed")
        self.assertEqual(vals["result"], "F1 processat")
        self.assertFalse(vals["error"])
        self.assertEqual(vals["generated_invoice_ids"], [(6, 0, [31, 32])])
        batch_obj._refresh_execution.assert_called_once_with(
            self.cursor, self.uid, 7, context={}
        )

    def test_persists_no_action_functional_outcome(self):
        batch_obj = mock.Mock()
        with mock.patch.object(self.pool, "get", return_value=batch_obj):
            with mock.patch.object(
                    self.line_obj, "read", return_value={"batch_id": [7, "F1_R-TASCA-7"]}):
                with mock.patch.object(self.line_obj, "write") as write:
                    self.line_obj._persist_line_outcome(
                        self.cursor,
                        self.uid,
                        3,
                        result={"status": "no_action", "messages": ["No s'actua."]},
                        context={},
                    )

        vals = write.call_args[0][3]
        self.assertEqual(vals["state"], "done")
        self.assertEqual(vals["outcome"], "no_action")

    def test_persists_technical_error_for_failed_line(self):
        batch_obj = mock.Mock()
        with mock.patch.object(self.pool, "get", return_value=batch_obj):
            with mock.patch.object(
                    self.line_obj, "read", return_value={"batch_id": [7, "F1_R-TASCA-7"]}):
                with mock.patch.object(self.line_obj, "write") as write:
                    self.line_obj._persist_line_outcome(
                        self.cursor,
                        self.uid,
                        3,
                        error=ValueError("Unexpected error"),
                        context={},
                    )

        vals = write.call_args[0][3]
        self.assertEqual(vals["state"], "failed")
        self.assertFalse(vals["outcome"])
        self.assertEqual(vals["error"], "Unexpected error")

    def test_refreshes_derived_counts_state_and_csv(self):
        line_obj = mock.Mock()
        line_obj.search.return_value = [1, 2, 3]
        first_line = mock.Mock()
        first_line.sequence = 1
        first_line.f1_id.id = 11
        first_line.state = "done"
        first_line.outcome = "processed"
        first_line.generated_invoice_ids = []
        first_line.result = "F1 processat"
        first_line.error = False
        second_line = mock.Mock()
        second_line.sequence = 2
        second_line.f1_id.id = 12
        second_line.state = "failed"
        second_line.outcome = False
        second_line.generated_invoice_ids = []
        second_line.result = False
        second_line.error = "Error tecnic"
        third_line = mock.Mock()
        third_line.sequence = 3
        third_line.f1_id.id = 13
        third_line.state = "done"
        third_line.outcome = "no_action"
        third_line.generated_invoice_ids = []
        third_line.result = "No s'actua."
        third_line.error = False
        line_obj.browse.return_value = [first_line, second_line, third_line]
        batch = mock.Mock()
        batch.name = "F1_R-TASCA-7"
        batch.state = "running"
        attachment_obj = mock.Mock()
        attachment_obj.create.return_value = 30
        attachment_obj.search.return_value = []
        with mock.patch.object(
                self.pool,
                "get",
                side_effect=lambda model: {
                    "refund.rectify.batch.line": line_obj,
                    "ir.attachment": attachment_obj,
                }[model]):
            with mock.patch.object(self.batch_obj, "browse", return_value=batch):
                with mock.patch.object(self.batch_obj, "write") as write:
                    self.batch_obj._refresh_execution(
                        self.cursor, self.uid, 7, context={}
                    )

        vals = write.call_args[0][3]
        self.assertEqual(vals["state"], "failed")
        self.assertEqual(vals["total_lines"], 3)
        self.assertEqual(vals["completed_lines"], 2)
        self.assertEqual(vals["failed_lines"], 1)
        self.assertEqual(vals["blocked_lines"], 0)
        attachment_vals = attachment_obj.create.call_args[0][2]
        self.assertEqual(attachment_vals["name"], "F1_R-TASCA-7.csv")
        self.assertEqual(attachment_vals["res_model"], "refund.rectify.batch")
        csv_content = base64.b64decode(attachment_vals["datas"])
        self.assertTrue("Error tecnic" in csv_content)
        self.assertTrue("outcome" in csv_content)
        self.assertTrue("processed" in csv_content)
        self.assertTrue("no_action" in csv_content)
