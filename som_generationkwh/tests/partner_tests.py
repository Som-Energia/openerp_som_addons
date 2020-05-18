# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from destral.patch import PatchNewCursors
import netsvc
import time
import random


class PartnerTests(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool
        self.imd_obj = self.pool.get('ir.model.data')
        self.emission_obj = self.pool.get('generationkwh.emission')
        self.investment_obj = self.pool.get('generationkwh.investment')
        self.partner_obj = self.pool.get('res.partner')
        self.IrModelData = self.openerp.pool.get('ir.model.data')
        self.GenerationkWhAssignment = self.openerp.pool.get('generationkwh.assignment')
        self.GiscedataPolissa = self.openerp.pool.get('giscedata.polissa')
        #self.txn = Transaction().start(self.database)

    def tearDown(self):
        #self.txn.stop()
        pass


    def test__clean_iban__beingCanonical(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.clean_iban(cursor, uid, "ABZ12345"),
                "ABZ12345")

    def test__clean_iban__havingLower(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.clean_iban(cursor, uid, "abc123456"),
                "ABC123456")

    def test__clean_iban__weirdSymbols(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.clean_iban(cursor, uid, "ABC:12.3 4-5+6"),
                "ABC123456")

    def test__check_iban__valid(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.check_iban(cursor, uid, 'ES7712341234161234567890'),
                'ES7712341234161234567890')

    def test__check_iban__valid_oriol(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.check_iban(cursor, uid, 'ES5831831700680000909309'),
                'ES5831831700680000909309')

    def test__check_iban__notNormalized(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.check_iban(cursor, uid, 'ES77 1234-1234.16 1234567890'),
                'ES7712341234161234567890')

    def test__check_iban__badIbanCrc(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.check_iban(cursor, uid, 'ES8812341234161234567890'),
                False)

    def test__check_iban__goodIbanCrc_badCCCCrc(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                self.investment_obj.check_iban(cursor, uid, 'ES0212341234001234567890'),
                False)

    def test__check_iban__fromForeignCountry_notAcceptedYet(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            self.assertEqual(
                # Arabian example from wikipedia
                self.investment_obj.check_iban(cursor, uid, 'SA03 8000 0000 6080 1016 7519'),
                False)

    def test__www_generationkwh_investments__twoGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_list = self.partner_obj.www_generationkwh_investments(cursor, uid, partner_id)

            for inv in inv_list:
                inv.pop('id')
            self.assertEquals(inv_list, [
                {'nominal_amount': 1000.0, 'first_effective_date': False, 
                    'name': u'GKWH00001', 'last_effective_date': False, 'draft': True,
                    'purchase_date': False, 'member_id': (1, u'Gil, Pere'), 'active': True,
                    'order_date': '2019-10-01', 'amortized_amount': 0.0, 'nshares': 10},
                {'nominal_amount': 1000.0, 'first_effective_date': '2020-10-12', 
                    'name': u'GKWH00002', 'last_effective_date': '2044-10-12', 'draft': True,
                    'purchase_date': '2019-10-12', 'member_id': (1, u'Gil, Pere'), 'active': True,
                    'order_date': '2019-10-01', 'amortized_amount': 0.0, 'nshares': 10}
            ])

    def test__www_aportacions_investments__twoAPO(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                        cursor, uid, 'som_generationkwh', 'res_partner_inversor1'
                        )[1]

            inv_list = self.partner_obj.www_aportacions_investments(cursor, uid, partner_id)

            for inv in inv_list:
                inv.pop('id')
            self.assertEquals(inv_list, [
                {'nominal_amount': 1000.0, 'first_effective_date': False, 'name': u'APO00001',
                    'last_effective_date': False, 'draft': True, 'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'), 'active': True, 'order_date': '2020-03-04',
                    'amortized_amount': 0.0, 'nshares': 10},
                {'nominal_amount': 5000.0, 'first_effective_date': False, 'name': u'APO00002',
                    'last_effective_date': False, 'draft': True, 'purchase_date': False,
                    'member_id': (1, u'Gil, Pere'), 'active': True, 'order_date': '2020-06-01',
                    'amortized_amount': 0.0, 'nshares': 50}
            ])

    def test__www_generationkwh_assignments__twoGKWH(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            partner_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'res_partner_inversor1')[1]
            member_id = self.IrModelData.get_object_reference(
                cursor, uid, 'som_generationkwh', 'soci_0001')[1]
            polissa_id = self.IrModelData.get_object_reference(
                cursor, uid, 'giscedata_polissa', 'polissa_0001')[1]
            self.GenerationkWhAssignment.create(cursor, uid, {'member_id': member_id,
                'contract_id': polissa_id, 'priority': 0})

            assig_list = self.partner_obj.www_generationkwh_assignments(cursor, uid, partner_id)

            for a in assig_list:
                a.pop('id')
            self.assertEquals(assig_list, [{'annual_use_kwh': False,
                'contract_address': u'carrer inventat 1 1 1 1 aclaridor 00001 (Poble de Prova)',
                'contract_id': 1, 'contract_last_invoiced': False, 'contract_name': u'0001C',
                'contract_state': u'esborrany', 'member_id': 1, 'member_name': u'Gil, Pere',
                'priority': 0}])

# vim: et ts=4 sw=4
