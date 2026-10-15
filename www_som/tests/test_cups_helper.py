# -*- coding: utf-8 -*-
from __future__ import absolute_import

from mock import patch

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

    def test_get_polissa_id_delegates_to_private_method(self):
        cups_helper_obj = self.pool.get("cups.helper")
        context = {"active_test": False}
        with patch.object(
            type(cups_helper_obj), "_get_polissa_id", return_value=42
        ) as get_polissa_id:
            result = cups_helper_obj.get_polissa_id(
                self.cursor, self.uid, 1, context=context
            )

        self.assertEqual(result, 42)
        get_polissa_id.assert_called_once_with(
            self.cursor, self.uid, 1, context=context
        )

    def test_check_cups_without_contract_preserves_address(self):
        cups_helper_obj = self.pool.get("cups.helper")
        cups_obj = self.pool.get("giscedata.cups.ps")
        polissa_obj = self.pool.get("giscedata.polissa")
        cups_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_01"
        )[1]
        cups = cups_obj.browse(self.cursor, self.uid, cups_id)

        with patch.object(type(polissa_obj), "search", return_value=[]):
            cups_data = cups_helper_obj._get_cups_data(
                self.cursor, self.uid, cups_id
            )
            with patch.object(
                type(polissa_obj), "www_get_distributor_id", return_value=False
            ):
                result = cups_helper_obj.check_cups(
                    self.cursor, self.uid, cups.name, context={}
                )

        self.assertEqual(cups_data, {"address": cups.nv})
        self.assertEqual(result["address"], cups.nv)
        self.assertEqual(result["status"], "inactive")
        self.assertEqual(result["tariff_type"], "")
        self.assertEqual(result["tariff_name"], "")

    def test_check_inexistent_cups(self):
        cups_helper_obj = self.pool.get("cups.helper")

        # CUPS no existent
        cups_name = "ES0000000000000000"
        status = cups_helper_obj.check_cups(
            self.cursor, self.uid, cups_name, context={}
        )
        resulting_dictionary = {
            "cups": cups_name,
            "status": "new",
            "tariff_type": "",
            "tariff_name": "",
            "address": "",
            "knowledge_of_distri": False,
        }
        self.assertEqual(status, resulting_dictionary)

    def test_check_existent_cups(self):
        cups_obj = self.pool.get("giscedata.cups.ps")
        cups_helper_obj = self.pool.get("cups.helper")
        polissa_obj = self.pool.get("giscedata.polissa")
        cups_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_01"
        )[1]

        cups = cups_obj.browse(
            self.cursor, self.uid, cups_id, context={}
        )
        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0006"
        )[1]

        polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], [
            "validar", "contracte"
        ])

        # CUPS existent
        result = cups_helper_obj.check_cups(
            self.cursor, self.uid, cups.name, context={}
        )

        resulting_dictionary = {
            "cups": cups.name,
            "status": "active",
            "tariff_type": u"atr",
            "knowledge_of_distri": False,
            "address": u"carrer inventat",
            "tariff_name": u"2.0A",
        }

        self.assertEqual(result, resulting_dictionary)
