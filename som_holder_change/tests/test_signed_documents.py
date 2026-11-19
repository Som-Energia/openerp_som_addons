# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64

import mock
from destral import testing


class TestHolderChangeSignedDocuments(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestHolderChangeSignedDocuments, self).setUp()
        self.request_obj = self.openerp.pool.get("som.holder.change.request")
        self.process_obj = self.openerp.pool.get("giscedata.signatura.process")
        self.attachment_obj = self.openerp.pool.get("ir.attachment")
        imd_obj = self.openerp.pool.get("ir.model.data")
        self.polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]
        self.result_polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]

    def create_request(self, owner_change_type="T", with_mandate=True, status="completed"):
        filenames = ["contract-with-summary.pdf"]
        if with_mandate:
            filenames.append("bank-authorization.pdf")
        process_id = self.process_obj.create(
            self.cursor, self.uid,
            {"subject": "Holder change", "provider": "signaturit", "lang": "en_US",
             "signature_id": "provider-process", "status": status,
             "files": [(0, 0, {
                 "filename": filename, "doc_file": base64.b64encode(b"%PDF-original"),
                 "signature_id": "document-{}".format(index),
                 "status": "completed" if status == "completed" else "signing",
             }) for index, filename in enumerate(filenames)]},
        )
        return self.request_obj.create(
            self.cursor, self.uid,
            {"polissa_id": self.polissa_id, "cups": "ES123",
             "owner_change_type": owner_change_type, "state": "queued", "payload": {},
             "signature_process_id": process_id},
        )

    def attachments(self, model, resource_id):
        return self.attachment_obj.search(
            self.cursor, self.uid, [("res_model", "=", model), ("res_id", "=", resource_id)]
        )

    def test_signature_update_archives_signed_pdfs_on_request_once(self):
        request_id = self.create_request()
        process_id = self.request_obj.browse(
            self.cursor, self.uid, request_id
        ).signature_process_id.id
        with mock.patch.object(self.process_obj, "update_info", return_value=True):
            with mock.patch.object(
                self.process_obj, "signed_document", return_value=b"%PDF-signed"
            ) as download:
                self.process_obj.update(self.cursor, self.uid, [process_id])
                self.process_obj.update(self.cursor, self.uid, [process_id])
        self.assertEqual(download.call_count, 2)
        for call in download.call_args_list:
            self.assertEqual(call[1]["context"]["provider"], "signaturit")
        attachment_ids = self.attachments("som.holder.change.request", request_id)
        self.assertEqual(len(attachment_ids), 2)
        for attachment in self.attachment_obj.browse(self.cursor, self.uid, attachment_ids):
            self.assertEqual(base64.b64decode(attachment.datas), b"%PDF-signed")
        documents = self.openerp.pool.get("giscedata.signatura.documents").read(
            self.cursor, self.uid,
            self.process_obj.read(self.cursor, self.uid, process_id, ["files"])["files"],
            ["doc_file"], context={"bin_size": False},
        )
        self.assertTrue(all(
            base64.b64decode(document["doc_file"]) == b"%PDF-original" for document in documents
        ))

    def test_execute_copies_signed_pdfs_once_for_transfer_and_subrogation(self):
        for owner_change_type in ("T", "S"):
            request_id = self.create_request(owner_change_type=owner_change_type)
            with mock.patch.object(
                self.process_obj, "signed_document", return_value=b"%PDF-signed"
            ):
                source_ids = self.request_obj._archive_signed_documents(
                    self.cursor, self.uid, request_id
                )
            self.attachment_obj.create(
                self.cursor, self.uid,
                {"name": "not-a-signed-document.pdf", "datas": base64.b64encode(b"other"),
                 "res_model": "som.holder.change.request", "res_id": request_id},
            )
            with mock.patch.object(self.request_obj, "_notify_completed_request"):
                with mock.patch.object(
                    self.request_obj, "_run_holder_change",
                    return_value=(False, self.result_polissa_id, False, False),
                ) as execute:
                    with mock.patch.object(self.process_obj, "signed_document") as download:
                        self.request_obj.execute(self.cursor, self.uid, request_id)
                        self.request_obj.execute(self.cursor, self.uid, request_id)
            execute.assert_called_once()
            download.assert_not_called()
            for source in self.attachment_obj.browse(self.cursor, self.uid, source_ids):
                copied_ids = self.attachment_obj.search(
                    self.cursor, self.uid,
                    [("res_model", "=", "giscedata.polissa"),
                     ("res_id", "=", self.result_polissa_id),
                     ("description", "=", source.description)],
                )
                self.assertEqual(len(copied_ids), 1)
                copied = self.attachment_obj.browse(self.cursor, self.uid, copied_ids[0])
                self.assertEqual(copied.datas, source.datas)
                self.assertEqual(copied.datas_fname, source.datas_fname)
            self.assertEqual(len(self.attachments("som.holder.change.request", request_id)), 3)

    def test_card_request_archives_only_contract(self):
        request_id = self.create_request(with_mandate=False)
        with mock.patch.object(
            self.process_obj, "signed_document", return_value=b"%PDF-signed"
        ) as download:
            ids = self.request_obj._archive_signed_documents(
                self.cursor, self.uid, request_id
            )
        download.assert_called_once()
        self.assertEqual(len(ids), 1)

    def test_pending_signature_does_not_archive_unsigned_documents(self):
        request_id = self.create_request(status="doing")
        with mock.patch.object(self.process_obj, "signed_document") as download:
            self.assertEqual(self.request_obj._archive_signed_documents(
                self.cursor, self.uid, request_id
            ), [])
        download.assert_not_called()
        self.assertFalse(self.attachments("som.holder.change.request", request_id))

    def test_failed_download_can_be_retried(self):
        request_id = self.create_request(with_mandate=False)
        with mock.patch.object(
            self.process_obj, "signed_document", side_effect=Exception("Provider unavailable")
        ):
            with self.assertRaises(Exception):
                self.request_obj._archive_signed_documents(self.cursor, self.uid, request_id)
        self.assertFalse(self.attachments("som.holder.change.request", request_id))
        with mock.patch.object(
            self.process_obj, "signed_document", return_value=b"%PDF-signed"
        ):
            self.assertEqual(len(self.request_obj._archive_signed_documents(
                self.cursor, self.uid, request_id
            )), 1)
