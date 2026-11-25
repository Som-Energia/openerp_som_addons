# -*- coding: utf-8 -*-
from __future__ import absolute_import

import mock
from destral import testing


class TestHolderChangeAutomaticProcessing(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestHolderChangeAutomaticProcessing, self).setUp()
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        self.www_obj = self.openerp.pool.get("som.holder.change.www")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

    def create_request(self, state="awaiting_signature", signature_status="completed"):
        process_id = False
        if signature_status:
            process_id = self.openerp.pool.get("giscedata.signatura.process").create(
                self.cursor, self.uid,
                {"subject": "Holder change", "status": signature_status},
            )
        return self.request_obj.create(
            self.cursor, self.uid,
            {"polissa_id": self.polissa_id, "cups": "ES123",
             "owner_change_type": "T", "state": state, "payload": {},
             "signature_process_id": process_id},
        )

    def run_cron(self):
        # Keep the test transaction intact while exercising real eligibility
        # queries and the endpoint with isolated-cursor boundaries.
        db = mock.MagicMock()
        db.cursor.return_value.__enter__.return_value = self.cursor
        incoming_cursor = mock.Mock(dbname=self.cursor.dbname)
        with mock.patch(
            "som_holder_change.models.holder_change_request.pooler.get_db",
            return_value=db,
        ):
            with mock.patch.object(self.cursor, "commit"):
                with mock.patch.object(self.cursor, "rollback"):
                    self.request_obj.process_signed_requests_cron(
                        incoming_cursor, self.uid, [], context={"lang": "ca_ES"}
                    )
        self.assertEqual(db.cursor.call_count, db.cursor.return_value.__exit__.call_count)

    def test_cron_queues_only_signed_pending_requests_once(self):
        request_id = self.create_request()
        excluded_ids = []
        for status in ("wait", "doing", "unsend", "expired", "canceled", "declined", "error"):
            excluded_ids.append(self.create_request(signature_status=status))
        excluded_ids.append(self.create_request(signature_status=False))
        for state in (
            "received", "awaiting_payment", "validation_error",
            "queued", "completed", "execution_error",
        ):
            excluded_ids.append(self.create_request(state=state))

        with mock.patch.object(self.www_obj, "execute_request_async") as enqueue:
            self.run_cron()
            # A subsequent scheduled run or manual click must not enqueue twice.
            self.request_obj.check_signature_and_execute(
                self.cursor, self.uid, [request_id]
            )
            self.run_cron()
        enqueued_ids = [call[0][2] for call in enqueue.call_args_list]
        self.assertEqual(enqueued_ids.count(request_id), 1)
        self.assertFalse(set(enqueued_ids).intersection(excluded_ids))
        self.assertEqual(self.request_obj.read(
            self.cursor, self.uid, request_id, ["state"]
        )["state"], "queued")

    def test_cron_picks_up_signature_when_it_completes(self):
        request_id = self.create_request(signature_status="doing")
        with mock.patch.object(self.www_obj, "execute_request_async") as enqueue:
            self.run_cron()
            self.assertNotIn(request_id, [call[0][2] for call in enqueue.call_args_list])
            process_id = self.request_obj.browse(
                self.cursor, self.uid, request_id
            ).signature_process_id.id
            self.openerp.pool.get("giscedata.signatura.process").write(
                self.cursor, self.uid, [process_id], {"status": "completed"}
            )
            self.run_cron()
        self.assertEqual(
            [call[0][2] for call in enqueue.call_args_list].count(request_id), 1
        )

    def test_cron_continues_after_enqueue_failure(self):
        failed_id = self.create_request()
        next_id = self.create_request()

        def enqueue(cursor, uid, request_id, context=None):
            if request_id == failed_id:
                raise Exception("Queue unavailable")
            return True

        with mock.patch.object(
            self.www_obj, "execute_request_async", side_effect=enqueue
        ) as dispatch:
            self.run_cron()
        self.assertIn(next_id, [call[0][2] for call in dispatch.call_args_list])
        failed = self.request_obj.read(
            self.cursor, self.uid, failed_id, ["state", "error_code"]
        )
        self.assertEqual(failed["state"], "awaiting_signature")
        self.assertEqual(failed["error_code"], "QUEUE_ERROR")

    def test_cron_is_disabled_and_scheduled_every_minute(self):
        cron_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_holder_change", "ir_cron_process_signed_holder_changes"
        )[1]
        cron = self.openerp.pool.get("ir.cron").read(
            self.cursor, self.uid, cron_id,
            ["active", "interval_number", "interval_type", "model", "function"],
        )
        self.assertFalse(cron["active"])
        self.assertEqual(cron["interval_number"], 1)
        self.assertEqual(cron["interval_type"], "minutes")
        self.assertEqual(cron["model"], "som.holder.change.request")
        self.assertEqual(cron["function"], "process_signed_requests_cron")
