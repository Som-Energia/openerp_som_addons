# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json

from destral import testing
from destral.transaction import Transaction
from giscedata_switching.tests.common_tests import TestSwitchingImport
from lxml import etree


class TestSwitchingTelefon(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestSwitchingTelefon, self).setUp()
        self.address_obj = self.openerp.pool.get('res.partner.address')
        self.telefon_obj = self.openerp.pool.get('giscedata.switching.telefon')
        self.mod_con_wizard_obj = self.openerp.pool.get(
            'giscedata.switching.mod.con.wizard'
        )
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

    def test_mod_con_wizard_uses_structured_phone_prefix(self):
        self.address_obj.write(self.cursor, self.uid, [1], {
            'phone': '1234567890',
            'phone_prefix': self.get_prefix('850'),
            'mobile': False,
            'mobile_prefix': False,
        })

        phone = self.mod_con_wizard_obj.get_phone(
            self.cursor, self.uid, 1
        )

        self.assertEqual(phone['phone_pre'], '850')
        self.assertEqual(phone['phone_num'], '1234567890')

    def test_mod_con_wizard_phone_prefix_allows_three_digits(self):
        self.assertEqual(
            self.mod_con_wizard_obj._columns['phone_pre'].size, 4
        )


class TestStructuredATRPhoneXML(TestSwitchingImport):

    @staticmethod
    def xml_telephone_values(xml):
        document = etree.fromstring(xml)
        return [
            (
                phone.xpath('./*[local-name()="PrefijoPais"]/text()')[0],
                phone.xpath('./*[local-name()="Numero"]/text()')[0],
            )
            for phone in document.xpath('//*[local-name()="Telefono"]')
        ]

    def get_prefix(self, cursor, uid, code):
        return self.openerp.pool.get('ir.model.data').get_object_reference(
            cursor, uid, 'base_extended_som',
            'res_phone_national_code_data_{}'.format(code)
        )[1]

    def set_contract_holder_phone(self, cursor, uid, contract_id):
        contract = self.openerp.pool.get('giscedata.polissa').browse(
            cursor, uid, contract_id
        )
        self.openerp.pool.get('res.partner.address').write(
            cursor, uid, [contract.titular.address[0].id], {
                'phone': '1234567890',
                'phone_prefix': self.get_prefix(cursor, uid, '850'),
                'mobile': False,
                'mobile_prefix': False,
            }
        )

    def test_c1_creation_uses_dummy_phone_in_generated_xml(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.switch(txn, 'comer')
            contract_id = self.get_contract_id(txn)
            self.activar_polissa_CUPS(txn)
            self.set_contract_holder_phone(cursor, uid, contract_id)

            step_id = self.create_case_and_step(
                cursor, uid, contract_id, 'C1', '01'
            )
            step_obj = self.openerp.pool.get('giscedata.switching.c1.01')
            c101 = step_obj.browse(cursor, uid, step_id)
            xml = step_obj.generar_xml(cursor, uid, step_id)[1]

            self.assertEqual(
                (c101.telefons[0].prefix, c101.telefons[0].numero),
                ('850', '1234567890')
            )
            self.assertIn(('850', '1234567890'), self.xml_telephone_values(xml))

    def test_c2_wizard_serializes_structured_contact_phone_in_xml(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.switch(txn, 'comer')
            contract_id = self.get_contract_id(txn)
            self.set_contract_holder_phone(cursor, uid, contract_id)
            wizard_obj = self.openerp.pool.get(
                'giscedata.switching.mod.con.wizard'
            )
            context = {'cas': 'C2', 'pol_id': contract_id}
            wizard_id = wizard_obj.create(cursor, uid, {}, context=context)
            wizard = wizard_obj.browse(cursor, uid, wizard_id)
            self.assertEqual(
                (wizard.phone_pre, wizard.phone_num), ('850', '1234567890')
            )
            wizard_obj.write(cursor, uid, [wizard_id], {
                'change_atr': True,
                'change_adm': False,
                'activacio_cicle': 'L',
            }, context=context)
            wizard_obj.genera_casos_atr(
                cursor, uid, [wizard_id], context=context
            )

            wizard = wizard_obj.browse(cursor, uid, wizard_id)
            switching_id = json.loads(wizard.casos_generats)[0]
            switching = self.openerp.pool.get('giscedata.switching').browse(
                cursor, uid, switching_id
            )
            c201 = switching.get_pas()
            xml = c201.generar_xml()[1]

            self.assertEqual(
                (c201.cont_telefons[0].prefix, c201.cont_telefons[0].numero),
                ('850', '1234567890')
            )
            self.assertIn(('850', '1234567890'), self.xml_telephone_values(xml))
