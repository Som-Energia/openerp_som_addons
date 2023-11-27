# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class ReportBackendMailcanvipreusTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.Polissa = self.openerp.pool.get('giscedata.polissa')
        self.Enviament = self.openerp.pool.get('som.enviament.massiu')
        self.Backend = self.openerp.pool.get('report.backend.mailcanvipreus')

    def tearDown(self):
        self.txn.stop()

    def test__get_preus(self):

        pol_id = self.IrModelData.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_tarifa_018'
        )[1]
        pol = self.Polissa.browse(self.cursor, self.uid, pol_id)

        res = self.Backend.get_preus(self.cursor, self.uid, pol, {'date': '2023-11-20'})

        self.assertEqual(res, {})
