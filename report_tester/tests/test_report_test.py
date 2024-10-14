# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestReportTest(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_something(self):
        """First line of docstring appears in test logs.
        Other lines do not.
        Any method starting with ``test_`` will be tested.
        """
        self.cursor
        self.uid
        self.openerp.pool.get('res.users')
        self.openerp.pool.get('ir.model.data')

        self.assertEqual(True, True)
