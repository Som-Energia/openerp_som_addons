from destral import testing
from destral.transaction import Transaction
from osv.orm import ValidateException


class TestSomenergiaSoci(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool

    def test_create_partner_twice_sameVAT__notAllowed(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            pool = self.openerp.pool
            Soci = pool.get("somenergia.soci")
            vals = {
                "name": "Test Name",
                "vat": "ES50030279N",
            }
            vals_duplicate = {"name": "Another Test Name", "vat": "ES50030279N"}
            Soci.create(cursor, uid, vals)
            with self.assertRaises(ValidateException):
                Soci.create(cursor, uid, vals_duplicate)

    def test_create_partner_firstCancelled__allowed(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            pool = self.openerp.pool
            Soci = pool.get("somenergia.soci")
            vals = {
                "name": "Test Name",
                "vat": "ES50030279N",
                "baixa": True,
                "data_baixa_soci": "2020-01-01",
            }
            Soci.create(cursor, uid, vals)

            vals_duplicate = {
                "name": "Another Test Name",
                "vat": "ES50030279N",
            }
            Soci.create(cursor, uid, vals_duplicate)

            number_socis = len(Soci.search(cursor, uid, [("vat", "=", "ES50030279N")]))
            self.assertEqual(number_socis, 2)

    def test_create_partner_withOutCancelDate__allowed(self):
        with Transaction().start(self.database) as txn:
            uid = txn.user
            cursor = txn.cursor
            pool = self.openerp.pool
            Soci = pool.get("somenergia.soci")
            vals = {
                "name": "Test Name",
                "vat": "ES50030279N",
                "baixa": True,
            }
            Soci.create(cursor, uid, vals)

            vals_duplicate = {
                "name": "Another Test Name",
                "vat": "ES50030279N",
            }
            Soci.create(cursor, uid, vals_duplicate)

            number_socis = len(Soci.search(cursor, uid, [("vat", "=", "ES50030279N")]))
            self.assertEqual(number_socis, 2)
