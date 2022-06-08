# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction

class TestsPartnerAddress(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor, self.uid, self.pool = (self.txn.cursor, self.txn.user, self.openerp.pool)

    def tearDown(self):
        self.txn.stop()

    def test_fill_merge_fields_clients(self):
        partner_address_o = self.pool.get('res.partner.address')
        partner_o = self.pool.get('res.partner')
        imd_o = self.pool.get('ir.model.data')
        address_id = imd_o.get_object_reference(self.cursor, self.uid, 'base', 'res_partner_address_1')[1]
        partner_id = partner_address_o.read(self.cursor, self.uid, address_id, ['partner_id'])['partner_id'][0]

        municipi_id = imd_o.get_object_reference(self.cursor, self.uid, 'base_extended', 'ine_17160')[1]
        partner_address_o.write(self.cursor, self.uid, address_id, {'id_municipi': municipi_id})

        partner_o.write(self.cursor, self.uid, partner_id, {'lang':'en_US'})
        merge_fields = partner_address_o.fill_merge_fields_clients(self.cursor, self.uid, address_id)
        self.maxDiff = None
        self.assertDictEqual(merge_fields, {'email_address': u'info@openroad.be',
            'merge_fields': {'EMAIL': u'info@openroad.be',
            'FNAME': u'OpenRoad',
            'LNAME': u'OpenRoad',
            'MMERGE10': u'1000',
            'MMERGE3': u'en_US',
            'MMERGE9': u'OpenRoad',
            'MMERGE5': u'Sant Feliu de Gu\xedxols',
            'MMERGE6': u'Baix Empord\xe0',
            'MMERGE7': u'Girona',
            'MMERGE8': u'Catalu\xf1a',
            },
            'status': 'subscribed'}
        )