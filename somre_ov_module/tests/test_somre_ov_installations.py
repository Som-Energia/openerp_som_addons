# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from destral import testing
from destral.transaction import Transaction


class SomreOvInstallationsTests(testing.OOTestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.imd = self.pool.get('ir.model.data')
        self.polissa = self.pool.get('giscere.polissa')
        self.installation = self.pool.get('somre.ov.installations')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.maxDiff = None

    def tearDown(self):
        self.txn.stop()

    base_vat = 'ES48591264S'
    legal_vat = 'ESW2796397D'
    missing_vat = 'ES11111111H'
    no_contracts_vat = 'ES36464471H'
    no_installation_vat = 'TODO'
    no_coordinates__contract_number = '103'

    def activate_contracts(self, vat):
        contract_ids = self.polissa.search(self.cursor, self.uid, [('titular.vat', '=', vat)])
        self.polissa.write(self.cursor, self.uid, contract_ids, {'state': 'activa'})

    def test__get_installations__base(self):
        vat = self.base_vat
        self.activate_contracts(vat)

        result = self.installation.get_installations(self.cursor, self.uid, vat)

        expected_result = [
            dict(
                contract_number='103',
                installation_name='Installation 3',
            ),
        ]
        self.assertEqual(expected_result, result)

    def test__get_installations__multiple_installations(self):
        vat = self.legal_vat
        self.activate_contracts(vat)

        result = self.installation.get_installations(self.cursor, self.uid, vat)

        expected_result = [
            dict(
                contract_number='100',
                installation_name='Installation 0',
            ),
            dict(
                contract_number='101',
                installation_name='Installation 1',
            ),
            dict(
                contract_number='102',
                installation_name='Installation 2',
            ),
        ]
        self.assertEqual(expected_result, result)

    def test__get_installations__user_not_exists(self):
        vat = self.missing_vat
        self.activate_contracts(vat)

        result = self.installation.get_installations(self.cursor, self.uid, vat)

        self.assertEqual(result, dict(
            code='NoSuchUser',
            error='User does not exist',
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    # def test__get_installations__user_inactive(self):

    def reference(self, module, id):
        return self.imd.get_object_reference(
            self.cursor, self.uid, module, id,
        )[1]

    def test__get_installations__contract_with_no_related_installation(self):
        vat = self.no_contracts_vat
        self.activate_contracts(vat)

        result = self.installation.get_installations(self.cursor, self.uid, vat)

        self.assertEqual(result, [])

    def test__get_installation_details__base(self):
        contract_number = '101'
        vat = self.legal_vat
        self.activate_contracts(vat)

        result = self.installation.get_installation_details(
            self.cursor, self.uid, vat, contract_number)

        expected_result = dict(
            installation_details=dict(
                contract_number='101',
                name='Installation 1',
                address='Carrer Buenaventura Durruti 2 aclaridor 08080 (Girona)',
                city='Girona',
                postal_code='08080',
                province='Girona',
                coordinates='41.54670,0.80284',
                ministry_code='RE-00001',
                technology='b11',
                cil='ES1234000000000001JK1F002',
                rated_power=801.0,
                type='IT-00001',
            ),
            contract_details=dict(
                billing_mode='index',
                proxy_fee=1.5,
                cost_deviation='included',
                reduction_deviation=100.0,
                representation_type='indirecta_cnmc',
                iban='**** **** **** **** **** 5257',
                discharge_date='2022-02-22',
                status='activa',
            ),
        )
        self.assertEqual(expected_result, result)

    def test__get_installation_details__contract_not_exists(self):
        contract_number = 'non_existing_contract_number'
        vat = self.legal_vat

        result = self.installation.get_installation_details(
            self.cursor, self.uid, vat, contract_number)

        self.assertEqual(result, dict(
            code='ContractNotExists',
            error='Contract does not exist',
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    def test__get_installation_details__contract_with_no_installation(self):
        installation_obj = self.pool.get('giscere.instalacio')
        installation_id = self.reference('somre_ov_module', 'giscere_instalacio_1')
        installation_obj.unlink(self.cursor, self.uid, [installation_id])
        contract_number = '101'
        vat = self.legal_vat
        self.activate_contracts(vat)

        result = self.installation.get_installation_details(
            self.cursor, self.uid, vat, contract_number)

        self.assertEqual(result, dict(
            code='ContractWithoutInstallation',
            error="No installation found for contract '101'",
            contract_number='101',
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    def test__get_installation_details__coordinates_are_empty(self):
        contract_number = self.no_coordinates__contract_number
        vat = self.base_vat
        self.activate_contracts(vat)

        result = self.installation.get_installation_details(
            self.cursor, self.uid, vat, contract_number)

        expected_coordinates = None
        self.assertEqual(expected_coordinates, result['installation_details']['coordinates'])

    def test__get_installation_details__not_owner(self):
        contract_number = '101'  # belongs to legal_vat
        vat = self.base_vat
        self.activate_contracts(self.legal_vat)

        result = self.installation.get_installation_details(
            self.cursor, self.uid, vat, contract_number)

        self.assertEqual(result, dict(
            code='UnauthorizedAccess',
            error="User {vat} cannot access the Contract '{contract_number}'".format(
                vat=vat,
                contract_number=contract_number
            ),
            username=vat,
            resource_type="Contract",
            resource_name=contract_number,
            trace=result.get('trace', "TRACE IS MISSING"),
        ))

    # def test_get_installations___inactive_contracts_included_same_installation
