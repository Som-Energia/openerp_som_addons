# -*- coding: utf-8 -*-
import base64
import mock
from destral import testing
from destral.transaction import Transaction

_netsvc_local_service = (
    'som_polissa_condicions_generals.www.contract_helper.netsvc.LocalService'
)


class TestsContractHelper(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.helper = self.openerp.pool.get('contract.helper')
        imd = self.openerp.pool.get('ir.model.data')
        self.pol_id = imd.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

    def tearDown(self):
        self.txn.stop()

    @mock.patch(_netsvc_local_service)
    def test_get_contract_returns_base64(self, mock_local_service):
        fake_pdf = b'%PDF-fake-content'
        mock_local_service.return_value.create.return_value = (fake_pdf, 'pdf')

        result = self.helper.get_contract(
            self.cursor, self.uid, self.pol_id, context={}
        )

        self.assertIn('contracte', result)
        decoded = base64.b64decode(result['contracte'])
        self.assertEqual(decoded, fake_pdf)
