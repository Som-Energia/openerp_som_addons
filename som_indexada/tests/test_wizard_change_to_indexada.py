# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction

class TestChangeToIndexada(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def test_change_to_indexada_one_polissa(self):
        pass

    def test_change_to_indexada_one_polissa_with_auto(self):
        pass