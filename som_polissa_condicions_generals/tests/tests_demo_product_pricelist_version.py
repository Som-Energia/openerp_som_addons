# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from destral.transaction import Transaction


class TestDemoProductPricelistVersion(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.version_obj = self.openerp.pool.get('product.pricelist.version')
        self.imd_obj = self.openerp.pool.get('ir.model.data')

    def tearDown(self):
        self.txn.stop()

    def test_ensure_demo_tarifas_electricidad_version__reuses_overlapping_version(self):
        pricelist_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio', 'pricelist_tarifas_electricidad'
        )[1]
        before_ids = self.version_obj.search(
            self.cursor, self.uid, [('pricelist_id', '=', pricelist_id), ('active', '=', True)]
        )

        ensured_id = self.version_obj.ensure_demo_tarifas_electricidad_version(
            self.cursor, self.uid, context={}
        )
        after_ids = self.version_obj.search(
            self.cursor, self.uid, [('pricelist_id', '=', pricelist_id), ('active', '=', True)]
        )

        self.assertTrue(ensured_id in after_ids)
        self.assertEqual(len(after_ids), len(before_ids))
