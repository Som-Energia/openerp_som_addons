# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
import time
import random


class InvestmentTests(testing.OOTestCase):
    def test_mark_as_signed(self):
        """
        Checks if signed_date change
        :return:
        """
        pool = self.openerp.pool
        investment_obj = pool.get('generationkwh.investment')
        imd_obj = pool.get('ir.model.data')

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            inv_id = imd_obj.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'genkwh_0001'
                        )[1]
            inv_0001 = investment_obj.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, False)

            investment_obj.mark_as_signed(cursor, uid, inv_id, '2017-01-06')

            inv_0001 = investment_obj.browse(cursor, uid, inv_id)
            self.assertEquals(inv_0001.signed_date, '2017-01-06')

# vim: et ts=4 sw=4
