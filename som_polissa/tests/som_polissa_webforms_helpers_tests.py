# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import unittest
from osv import fields
import mock
from mock import Mock, ANY


class TestSomWebformsHelpersPolissa(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.helper_obj = self.openerp.pool.get("som.polissa.webforms.helpers")
        self.imd_obj = self.openerp.pool.get("ir.model.data")

    def tearDown(self):
        self.txn.stop()

    def _open_polissa(self, xml_ref):
        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa", xml_ref
        )[1]

        self.polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])

        return polissa_id

    def test_www_get_iban(self):
        polissa_id = self._open_polissa("polissa_domestica_0100")
        result = self.helper_obj.www_get_iban(self.cursor, self.uid, polissa_id)
        self.assertEqual(result, "**** **** **** **** **** 9397")

    def test_www_check_iban(self):
        correct_iban = "ES3120170806126133002095"
        incorrect_iban = "ES2222170806122222222222"
        result = self.helper_obj.www_check_iban(self.cursor, self.uid, correct_iban)
        self.assertEqual(result, correct_iban)
        result = self.helper_obj.www_check_iban(self.cursor, self.uid, incorrect_iban)
        self.assertEqual(result, False)

    def test_www_set_iban(self):
        polissa_id = self._open_polissa("polissa_domestica_0100")
        new_iban = "ES31 2017 0806 1261 3300 2095"
        result = self.helper_obj.www_set_iban(self.cursor, self.uid, polissa_id, new_iban)
        new_iban_pol = self.polissa_obj.read(self.cursor, self.uid, polissa_id, ["bank"])["bank"][1]
        self.assertEqual(new_iban_pol, new_iban)
