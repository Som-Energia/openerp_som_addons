# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
import time
import random


class EmissionTests(testing.OOTestCase):
    def test_change_emission_state(self):
        """
        Checks if when state changed, everithing works
        :return:
        """
        pool = self.openerp.pool
        emission_obj = pool.get('generationkwh.emission')
        imd_obj = pool.get('ir.model.data')

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            em_id = imd_obj.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_0001')[1]
            em_0001 = emission_obj.browse(cursor, uid, em_id)

            emission_obj.action_open(cursor, uid, em_id)

            self.assertEquals(em_0001.state, "open")


# vim: et ts=4 sw=4
