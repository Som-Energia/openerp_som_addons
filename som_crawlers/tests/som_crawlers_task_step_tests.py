# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import os


class SomCrawlersTaskStepTests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.model_data = self.pool.get("ir.model.data")
        self.ir_attachment = self.pool.get("ir.attachment")
        self.task = self.pool.get("som.crawlers.task")
        self.task_step = self.pool.get("som.crawlers.task.step")
        self.result = self.pool.get("som.crawlers.result")
        self.pathFileActual = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

    def tearDown(self):
        pass

    def test_attach_file_ok(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            result_id = self.model_data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_1"
            )[1]
            os.system("mkdir " + self.pathFileActual + "/demo/screenshots")
            os.system(
                "cp "
                + self.pathFileActual
                + "/demo/anselmo_2022-07-26_15_11_GRCW_W4X151_20220726151137.zip "
                + self.pathFileActual
                + "/demo/screenshots/screenshots.zip"
            )

            attachment_id = self.task_step.attach_file(
                cursor, uid, self.pathFileActual + "/demo/screenshots", "screenshots.zip", result_id
            )

            self.assertTrue(attachment_id)
            self.assertTrue(
                self.ir_attachment.search(
                    cursor,
                    uid,
                    [
                        ("name", "=", "screenshots.zip"),
                        ("res_model", "=", "som.crawlers.result"),
                        ("res_id", "=", result_id),
                    ],
                )
            )
            self.assertFalse(
                os.path.exists(self.pathFileActual + "/demo/screenshots/screenshots.zip")
            )

    def test_attach_file_not_exist(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            result_id = self.model_data.get_object_reference(
                cursor, uid, "som_crawlers", "demo_result_1"
            )[1]
            os.system("mkdir " + self.pathFileActual + "/demo/screenshots")

            with self.assertRaises(IOError) as context:
                self.task_step.attach_file(
                    cursor,
                    uid,
                    self.pathFileActual + "/demo/screenshots",
                    "screenshots.zip",
                    result_id,
                )

                self.assertTrue(
                    "IOError: [Errno 2] No such file or directory: " in context.exception
                )
