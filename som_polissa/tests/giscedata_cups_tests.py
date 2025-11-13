# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class TestGiscedataCups(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.cups_obj = self.model("giscedata.cups.ps")

    def tearDown(self):
        self.txn.stop()

    def test_get_autoconsum_description(self):
        """
        Test the get_autoconsum_description method of the polissa model.
        """
        autoconsum = self.cups_obj.get_autoconsum_description(self.cursor, self.uid, '00', "ca_ES")
        self.assertEqual(autoconsum, u"00 - Sense Autoconsum")
        autoconsum = self.cups_obj.get_autoconsum_description(self.cursor, self.uid, '12', "es_ES")
        self.assertEqual(autoconsum, u"12 - Con excedentes")

    def test_get_auto_tipus_subseccio_description(self):
        """
        Test the get_auto_tipus_subseccio_description method of the polissa model.
        """
        tipus_subseccio = self.cups_obj.get_auto_tipus_subseccio_description(
            self.cursor, self.uid, "10", "ca_ES")
        self.assertEqual(tipus_subseccio, u"10 - Sense excedents No acollit a compensació")
        tipus_subseccio = self.cups_obj.get_auto_tipus_subseccio_description(
            self.cursor, self.uid, "0C", "es_ES")
        self.assertEqual(tipus_subseccio, u"0C - Baja como miembro de autoconsumo colectivo")
