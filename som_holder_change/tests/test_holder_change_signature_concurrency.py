# -*- coding: utf-8 -*-
from __future__ import absolute_import

from threading import Event, Thread
from uuid import uuid4

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import mock
import pooler
import psycopg2
from destral import testing
from destral.transaction import Transaction


class TestHolderChangeSignatureConcurrency(testing.OOTestCase):
    """Use real independent transactions: savepoint cursors cannot test locks."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.db = pooler.get_db(self.cursor.dbname)
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        self.www_obj = self.openerp.pool.get("som.holder.change.www")
        self.process_obj = self.openerp.pool.get("giscedata.signatura.process")
        self.subject = "Holder change concurrency {}".format(uuid4().hex)
        polissa_id = self.openerp.pool.get("ir.model.data").get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.cups = "ES0021126262693495FV"
        self.request_id = self.request_obj.create(self.cursor, self.uid, {
            "polissa_id": polissa_id, "cups": self.cups, "owner_change_type": "T",
            "state": "awaiting_signature", "contract_pdf": b"JVBERi0xLjQ=",
            "payload": {"contract_owner": {"lang": "en_US"}},
        })
        self.process_values = {
            "subject": self.subject, "provider": "signaturit", "lang": "en_US",
            "delivery_type": "url", "data": "{}", "template_res_id": self.request_id,
        }
        self.cursor.commit()

    def tearDown(self):
        try:
            self.cursor.rollback()
            process_ids = self.process_obj.search(
                self.cursor, self.uid, [("subject", "=", self.subject)]
            )
            self.request_obj.unlink(self.cursor, self.uid, [self.request_id])
            if process_ids:
                conversation_ids = [
                    process["conversation_id"][0]
                    for process in self.process_obj.read(
                        self.cursor, self.uid, process_ids, ["conversation_id"]
                    )
                ]
                self.process_obj.unlink(self.cursor, self.uid, process_ids)
                conversation_obj = self.openerp.pool.get("poweremail.conversation")
                remaining = conversation_obj.search(
                    self.cursor, self.uid, [("id", "in", conversation_ids)]
                )
                if remaining:
                    conversation_obj.unlink(self.cursor, self.uid, remaining)
            self.cursor.commit()
        finally:
            self.txn.stop()

    def test_concurrent_signing_creates_and_starts_only_one_process(self):
        self._check_concurrent_signing(existing_process=False)

    def test_concurrent_signing_starts_existing_process_only_once(self):
        self._check_concurrent_signing(existing_process=True)

    def _check_concurrent_signing(self, existing_process):
        if existing_process:
            process_id = self.process_obj.create(self.cursor, self.uid, self.process_values.copy())
            self.request_obj.write(
                self.cursor, self.uid, [self.request_id], {"signature_process_id": process_id}
            )
            self.cursor.commit()

        ready = Queue()
        provider_calls = Queue()
        results = Queue()
        errors = Queue()
        release_requests = Event()
        release_provider = Event()
        original_get_request = self.www_obj._get_request

        def synchronized_get_request(cursor, uid, request_id, cups, context=None):
            request = original_get_request(cursor, uid, request_id, cups, context=context)
            # Both callers must observe the same initial association before
            # either can register/start a process (including lazy browse data).
            bool(request.signature_process_id)
            ready.put(True)
            if not release_requests.wait(10):
                raise AssertionError("Concurrent signing callers did not synchronize")
            return request

        def start_provider(cursor, uid, ids, context=None):
            process_id = ids[0]
            if self.process_obj.read(cursor, uid, process_id, ["signature_id"])["signature_id"]:
                return True
            provider_calls.put(process_id)
            if not release_provider.wait(10):
                raise AssertionError("Signature startup was not released")
            self.process_obj.write(
                cursor, uid, [process_id], {"signature_id": "provider-{}".format(process_id)}
            )
            return True

        def sign():
            try:
                with self.db.cursor() as cursor:
                    results.put(self.www_obj.sign_request(
                        cursor, self.uid, self.request_id, self.cups
                    ))
            except Exception as error:
                errors.put(error)

        with mock.patch.object(self.www_obj, "_get_request", side_effect=synchronized_get_request):
            with mock.patch.object(
                self.www_obj, "_signature_process_values", return_value=self.process_values
            ):
                with mock.patch.object(
                    self.www_obj, "_wait_for_signature_documents", return_value=True
                ):
                    with mock.patch.object(self.process_obj, "start", side_effect=start_provider):
                        with mock.patch.object(
                            self.www_obj, "_wait_for_signature_url",
                            return_value="https://app.signaturit.com/document/concurrent",
                        ):
                            workers = [Thread(target=sign) for _index in range(2)]
                            for worker in workers:
                                worker.start()
                            try:
                                ready.get(timeout=10)
                                ready.get(timeout=10)
                                release_requests.set()
                                process_id = provider_calls.get(timeout=10)
                                self._assert_startup_holds_process_lock(process_id)
                            finally:
                                release_requests.set()
                                release_provider.set()
                                for worker in workers:
                                    worker.join(15)
                            self.assertFalse(any(worker.is_alive() for worker in workers))

        if not errors.empty():
            raise errors.get()
        self.assertEqual(results.qsize(), 2)
        self.assertEqual(results.get(), results.get())
        self.assertTrue(provider_calls.empty(), "The provider was started more than once")
        process_ids = self.process_obj.search(
            self.cursor, self.uid, [("subject", "=", self.subject)]
        )
        self.assertEqual(len(process_ids), 1)
        request = self.request_obj.read(
            self.cursor, self.uid, self.request_id, ["signature_process_id"]
        )
        self.assertEqual(request["signature_process_id"][0], process_ids[0])

    def _assert_startup_holds_process_lock(self, process_id):
        with self.db.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT id FROM giscedata_signatura_process WHERE id = %s FOR UPDATE NOWAIT",
                    (process_id,),
                )
            except psycopg2.Error as error:
                self.assertEqual(error.pgcode, "55P03")
                cursor.rollback()
            else:
                self.fail("Signature startup must hold the process row lock")
