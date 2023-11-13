
from destral import testing
from destral.transaction import Transaction
import unittest
from osv import fields
import mock
from mock import Mock, ANY

class TestGisceDataCups(testing.OOTestCase):

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.cups_obj = self.openerp.pool.get('giscedata.cups.ps')
        self.contract1_id = self.get_ref('giscedata_polissa', 'polissa_0001')
        self.contract2_id = self.get_ref('giscedata_polissa', 'polissa_autoconsum_03a')
        self.contract3_id = self.get_ref('som_polissa', 'polissa_domestica_0100')

    def tearDown(self):
        self.txn.stop()

    def get_ref(self, module, ref):
        IrModel = self.openerp.pool.get('ir.model.data')
        return IrModel._get_obj(
            self.cursor, self.uid,
            module, ref).id
