# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing


class TestSwitchingTelefon(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestSwitchingTelefon, self).setUp()
        self.address_obj = self.openerp.pool.get('res.partner.address')
        self.telefon_obj = self.openerp.pool.get('giscedata.switching.telefon')
        self.imd_obj = self.openerp.pool.get('ir.model.data')

    def get_prefix(self, code):
        return self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'base_extended_som',
            'res_phone_national_code_data_{}'.format(code)
        )[1]

    def test_structured_address_phones_keep_local_number_and_prefix(self):
        self.address_obj.write(self.cursor, self.uid, [1], {
            'phone': '1234567890',
            'phone_prefix': self.get_prefix('850'),
            'mobile': '987654321',
            'mobile_prefix': self.get_prefix('376'),
        })

        telephone_ids = self.telefon_obj.dummy_create(
            self.cursor, self.uid, 1
        )
        telephones = self.telefon_obj.read(
            self.cursor, self.uid, telephone_ids, ['numero', 'prefix']
        )

        self.assertEqual(
            [(telephone['numero'], telephone['prefix']) for telephone in telephones],
            [('1234567890', '850'), ('987654321', '376')]
        )

    def test_phone_without_structured_prefix_uses_legacy_cleaner(self):
        self.address_obj.write(self.cursor, self.uid, [1], {
            'phone': '612345678',
            'phone_prefix': False,
            'mobile': False,
            'mobile_prefix': False,
        })

        telephone_ids = self.telefon_obj.dummy_create(
            self.cursor, self.uid, 1
        )
        telephone = self.telefon_obj.read(
            self.cursor, self.uid, telephone_ids[0], ['numero', 'prefix']
        )

        self.assertEqual(
            (telephone['numero'], telephone['prefix']), ('612345678', '34')
        )
