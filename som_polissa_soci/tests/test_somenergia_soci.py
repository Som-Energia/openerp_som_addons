from destral import testing
from destral.transaction import Transaction
from osv.orm import ValidateException


class TestSomenergiaSoci(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor, self.uid, self.pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        conf_obj = self.pool.get('res.config')
        conf_obj.set(self.cursor, self.uid, 'deny_creating_duplicate_partners', 0)

    def tearDown(self):
        self.txn.stop()

    def test_create_partner_twice_sameVAT__notAllowed(self):
        Soci = self.pool.get("somenergia.soci")
        vals = {
            "name": "Test Name",
            "vat": "ES50030279N",
        }
        vals_duplicate = {"name": "Another Test Name", "vat": "ES50030279N"}
        Soci.create(self.cursor, self.uid, vals)
        with self.assertRaises(ValidateException):
            Soci.create(self.cursor, self.uid, vals_duplicate)

    def test_create_partner_firstCancelled__allowed(self):
        Soci = self.pool.get("somenergia.soci")
        vals = {
            "name": "Test Name",
            "vat": "ES50030279N",
            "baixa": True,
            "data_baixa_soci": "2020-01-01",
        }
        Soci.create(self.cursor, self.uid, vals)

        vals_duplicate = {
            "name": "Another Test Name",
            "vat": "ES50030279N",
        }
        Soci.create(self.cursor, self.uid, vals_duplicate)

        number_socis = len(Soci.search(self.cursor, self.uid, [("vat", "=", "ES50030279N")]))
        self.assertEqual(number_socis, 2)

    def test_create_partner_withOutCancelDate__allowed(self):
        Soci = self.pool.get("somenergia.soci")
        vals = {
            "name": "Test Name",
            "vat": "ES50030279N",
            "baixa": True,
        }
        Soci.create(self.cursor, self.uid, vals)

        vals_duplicate = {
            "name": "Another Test Name",
            "vat": "ES50030279N",
        }
        Soci.create(self.cursor, self.uid, vals_duplicate)

        number_socis = len(Soci.search(self.cursor, self.uid, [("vat", "=", "ES50030279N")]))
        self.assertEqual(number_socis, 2)
