# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import os
from datetime import datetime


class SomCrawlersTaskTests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.model_data = self.pool.get("ir.model.data")
        self.ir_attachment = self.pool.get("ir.attachment")
        self.task = self.pool.get("som.crawlers.task")
        self.task_step = self.pool.get("som.crawlers.task.step")
        self.holiday = self.pool.get("som.crawlers.holiday")
        self.result = self.pool.get("som.crawlers.result")
        self.pathFileActual = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

    def tearDown(self):
        pass

    def test__get_next_execution_date__normal_day(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            d = datetime(2022, 11, 9, 6, 30, 30)
            s = datetime(2022, 11, 9, 4, 50, 30)
            res = self.task.get_next_execution_date(cursor, uid, s, {"datetime_now": d})
            self.assertEquals(res, "2022-11-10 04:50:30")

    def test__get_next_execution_date__weekend_wend(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            d = datetime(2022, 11, 11, 6, 30, 30)
            s = datetime(2022, 11, 11, 4, 50, 30)
            res = self.task.get_next_execution_date(cursor, uid, s, {"datetime_now": d})
            self.assertEquals(res, "2022-11-14 04:50:30")

    def test__get_next_execution_date__weekend_sat(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            d = datetime(2022, 11, 12, 6, 30, 30)
            s = datetime(2022, 11, 12, 4, 50, 30)
            res = self.task.get_next_execution_date(cursor, uid, s, {"datetime_now": d})
            self.assertEquals(res, "2022-11-14 04:50:30")

    def test__get_next_execution_date__ree_holiday(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            d = datetime(2022, 10, 31, 6, 30, 30)
            s = datetime(2022, 10, 31, 4, 50, 30)
            res = self.task.get_next_execution_date(cursor, uid, s, {"datetime_now": d})
            self.assertEquals(res, "2022-11-02 04:50:30")

    def test__get_next_execution_date__staint_steve(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.holiday.create(
                cursor,
                uid,
                {
                    "date": "2022-12-26",
                    "desription": "saint steve",
                },
            )
            d = datetime(2022, 12, 23, 6, 30, 30)
            s = datetime(2022, 12, 23, 4, 50, 30)
            res = self.task.get_next_execution_date(cursor, uid, s, {"datetime_now": d})
            self.assertEquals(res, "2022-12-27 04:50:30")
