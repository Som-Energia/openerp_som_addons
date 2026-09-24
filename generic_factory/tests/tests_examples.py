# -*- coding: utf-8 -*-
from destral import testing


class TestAccountInvoiceSom(testing.OOTestCaseWithCursor):

    def test_create_partner(self):
        factory_obj = self.openerp.pool.get("generic.factory")
        partner_id = factory_obj.create(self.cursor, self.uid, 'res.partner', {})

        self.assertTrue(partner_id)

    def test_create_partner_withOverrides(self):
        factory_obj = self.openerp.pool.get("generic.factory")
        partner_id = factory_obj.create(
            self.cursor, self.uid, 'res.partner', {'name': "Test Partner"})

        self.assertTrue(partner_id)

        partner_data = self.openerp.pool.get("res.partner")
        partner = partner_data.browse(self.cursor, self.uid, partner_id)
        self.assertEqual(partner.name, "Test Partner")

    def test_create_polissa(self):
        factory_obj = self.openerp.pool.get("generic.factory")
        polissa_id = factory_obj.create(self.cursor, self.uid, 'giscedata.polissa', {})

        self.assertTrue(polissa_id)

        polissa_data = self.openerp.pool.get("giscedata.polissa")
        polissa = polissa_data.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(polissa.name, "Test Polissa")
