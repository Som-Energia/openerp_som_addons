# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
import time
import random


class EmissionTests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get('ir.model.data')
        self.emission_obj = self.pool.get('generationkwh.emission')
        #self.txn = Transaction().start(self.database)

    def tearDown(self):
        #self.txn.stop()
        pass

    def test__action_open(self):
        """
        Checks if when state changed, everithing works
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            em_id = self.imd_obj.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_0001')[1]
            em_0001 = self.emission_obj.browse(cursor, uid, em_id)

            self.emission_obj.action_open(cursor, uid, em_id)

            self.assertEquals(em_0001.state, "open")

    def test__set_done(self):
        """
        Checks if when state changed, everithing works
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            em_id = self.imd_obj.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_0001')[1]
            em_0001 = self.emission_obj.browse(cursor, uid, em_id)

            self.emission_obj.set_done(cursor, uid, em_id)

            self.assertEquals(em_0001.state, "done")

    def test__cancel(self):
        """
        Checks if when state changed, everithing works
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            em_id = self.imd_obj.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_0001')[1]
            em_0001 = self.emission_obj.browse(cursor, uid, em_id)

            self.emission_obj.cancel(cursor, uid, em_id)

            self.assertEquals(em_0001.state, "cancel")

    def test__set_to_draft(self):
        """
        Checks if when state changed, everithing works
        :return:
        """
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            em_id = self.imd_obj.get_object_reference(
                cursor, uid, 'som_generationkwh', 'emissio_0001')[1]
            em_0001 = self.emission_obj.browse(cursor, uid, em_id)

            self.emission_obj.set_to_draft(cursor, uid, em_id)

            self.assertEquals(em_0001.state, "draft")

# vim: et ts=4 sw=4
