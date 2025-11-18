# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestsCupsHelper(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.txn = Transaction().start(self.database)
        self.imd_obj = self.pool.get("ir.model.data")
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        pass

    def test_check_cups(self):
        cups_helper_obj = self.pool.get("cups.helper")
        cups_obj = self.pool.get("giscedata.cups.ps")

        # CUPS no existent
        cups_name = "ES0000000000000000"
        status = cups_helper_obj.check_cups(
            self.cursor, self.uid, cups_name, context={}
        )
        self.assertFalse(status)

        cups_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_01"
        )[1]

        cups = cups_obj.browse(
            self.cursor, self.uid, cups_id, context={}
        )

        # CUPS existent
        result = cups_helper_obj.check_cups(
            self.cursor, self.uid, cups.name, context={}
        )

        resulting_dictionary = {
            "cups": cups.name,
            "status": "active",
            "tariff_type": u"atr",
            "knowledge_of_distri": None,
        }

        self.assertEqual(result, resulting_dictionary)
