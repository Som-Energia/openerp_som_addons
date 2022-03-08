# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from expects import *
import mock


class SomAutoreclamaStatesTest(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def test_first_state_correct_dummy(self):
        sas_obj = self.get_model('som.autoreclama.state')
        first = sas_obj.browse(self.cursor, self.uid, 1)
        self.assertEqual(first.name, 'Correcte')
