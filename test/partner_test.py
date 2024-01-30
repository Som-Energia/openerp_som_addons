#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass
import datetime
from yamlns import namespace as ns
import erppeek_wst
import generationkwh.investmentmodel as gkwh
from generationkwh.testutils import assertNsEqual

@unittest.skipIf(not dbconfig, "depends on ERP")
class Partner_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Investment = self.erp.GenerationkwhInvestment
        self.Country = self.erp.ResCountry
        self.PaymentOrder = self.erp.PaymentOrder
        self.receiveMode = gkwh.investmentPaymentMode
        self.payMode = gkwh.amortizationPaymentMode

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    assertNsEqual=assertNsEqual

    def test__get_or_create_payment_order__badName(self):
        order_id = self.Investment.get_or_create_open_payment_order("BAD MODE")
        self.assertEqual(order_id, False)

    def test__get_or_create_payment_order__calledTwiceReturnsTheSame(self):
        first_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        second_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.assertEqual(first_order_id, second_order_id)

    def test__get_or_create_payment_order__noDraftCreatesANewOne(self):
        first_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.PaymentOrder.write(first_order_id, dict(
            state='done',
        ))
        second_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.assertNotEqual(first_order_id, second_order_id)

    def test__get_or_create_payment_order__properFieldsSet(self):
        first_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.PaymentOrder.write(first_order_id, dict(
            state='done',
        ))

        second_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        order = ns(self.PaymentOrder.read(second_order_id,[
            "date_prefered",
            "user_id",
            "state",
            "mode",
            "type",
            "create_account_moves",
        ]))
        order.user_id = order.user_id[0]
        order.mode = order.mode[1]
        self.assertNsEqual(order, """\
             id: {}
             create_account_moves: direct-payment
             date_prefered: fixed
             mode: GENERATION kWh
             state: draft
             type: receivable
             user_id: {}
            """.format(
                second_order_id,
                order.user_id,
            ))


    def test__get_or_create_payment_order__receivableInvoice(self):

        previous_order_id = self.Investment.get_or_create_open_payment_order(self.receiveMode)
        self.PaymentOrder.write(previous_order_id, dict(
            state='done',
        ))

        order_id = self.Investment.get_or_create_open_payment_order(
            self.receiveMode,
            True, #use_invoice
            )

        order = (self.PaymentOrder.read(order_id, ['create_account_moves','type']))
        order.pop('id')
        self.assertNsEqual(order, """\
                create_account_moves: bank-statement
                type: receivable
                """)

    def test__get_or_create_payment_order__payableInvoice(self):
        previous_order_id = self.Investment.get_or_create_open_payment_order(self.payMode)
        self.PaymentOrder.write(previous_order_id, dict(
            state='done',
        ))

        order_id = self.Investment.get_or_create_open_payment_order(
            self.payMode,
            True, #use_invoice
            )

        order = (self.PaymentOrder.read(order_id, ['create_account_moves','type']))
        order.pop('id')
        self.assertNsEqual(order, """\
                create_account_moves: bank-statement
                type: payable
                """)


    def test__get_or_create_partner_bank__whenExists(self):

        partner_id = self.personalData.partnerid
        expected = self.erp.ResPartnerBank.search([
            ('partner_id','=', partner_id),
            ])[0]
        iban = self.erp.ResPartnerBank.read(expected, [
            'iban',
            ])['iban']
        result = self.Investment.get_or_create_partner_bank(
            partner_id, iban)
        self.assertEqual(expected, result)

    def test__get_or_create_partner_bank__whenNew(self):

        partner_id = self.personalData.partnerid
        iban = 'ES8901825726580208779553'
        country_id = self.Country.search([('code', '=', 'ES')])[0]
        
        shouldBeNone = self.erp.ResPartnerBank.search([
            ('iban', '=', iban),
            ('partner_id','=',partner_id),
            ])
        self.assertFalse(shouldBeNone,
            "Partner already has such iban")

        result = self.Investment.get_or_create_partner_bank(
            partner_id, iban)

        self.assertTrue(result,
            "Should have been created")

        bank_id = self.erp.ResPartnerBank.search([
            ('iban', '=', iban),
            ('partner_id','=',partner_id),
            ])[0]
        self.assertEqual(bank_id, result)

        bank = ns(self.erp.ResPartnerBank.read(
            bank_id, [
            'name',
            'state',
            'iban',
            'partner_id',
            'country_id',
            'acc_country_id',
            'state_id',
            ]))
        for a in 'partner_id country_id acc_country_id state_id'.split():
            bank[a] = bank[a] and bank[a][0]

        self.assertNsEqual(bank, ns(
            id = bank_id,
            name = '',
            state = 'iban',
            iban = iban,
            partner_id = partner_id,
            country_id = country_id,
            acc_country_id = country_id,
            state_id = False,
            ))

    def test__check_spanish_account__lenghtNot20(self):
        self.assertEqual(
            self.Investment.check_spanish_account('1234161234567890'),
            False)

    def test__check_spanish_account__invalid(self):
        self.assertEqual(
            self.Investment.check_spanish_account('00001234061234567890'),
            False)

    def test__check_spanish_account__knownBank(self):
        self.assertEqual(
            self.Investment.check_spanish_account(
                '14911234761234567890'),
            dict(
                acc_number = '1491 1234 76 1234567890',
                bank_name = 'TRIODOS BANK',
            ))

    def test__check_spanish_account__unknownBank(self):
        self.assertEqual(
            self.Investment.check_spanish_account(
                '00001234161234567890'),
            dict(acc_number= "0000 1234 16 1234567890",))

    def test__check_spanish_account__nonDigitsIgnored(self):
        self.assertEqual(
            self.Investment.check_spanish_account(
                'E000F0-12:34161234567890'),
            dict(acc_number= "0000 1234 16 1234567890",))

    def test__clean_iban__beingCanonical(self):
        self.assertEqual(
            self.Investment.clean_iban("ABZ12345"),
            "ABZ12345")

    def test__clean_iban__havingLower(self):
        self.assertEqual(
            self.Investment.clean_iban("abc123456"),
            "ABC123456")

    def test__clean_iban__weirdSymbols(self):
        self.assertEqual(
            self.Investment.clean_iban("ABC:12.3 4-5+6"),
            "ABC123456")

    def test__check_iban__valid(self):
        self.assertEqual(
            self.Investment.check_iban('ES7712341234161234567890'),
            'ES7712341234161234567890')

    def test__check_iban__notNormalized(self):
        self.assertEqual(
            self.Investment.check_iban('ES77 1234-1234.16 1234567890'),
            'ES7712341234161234567890')

    def test__check_iban__badIbanCrc(self):
        self.assertEqual(
            self.Investment.check_iban('ES8812341234161234567890'),
            False)

    def test__check_iban__goodIbanCrc_badCCCCrc(self):
        self.assertEqual(
            self.Investment.check_iban('ES0212341234001234567890'),
            False)

    def test__check_iban__fromForeignCountry_notAcceptedYet(self):
        self.assertEqual(
            # Arabian example from wikipedia
            self.Investment.check_iban('SA03 8000 0000 6080 1016 7519'),
            False)


@unittest.skipIf(not dbconfig, "depends on ERP")
class PartnerInvestments_Test(unittest.TestCase):

    from generationkwh.testutils import assertNsEqual

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Soci = self.erp.SomenergiaSoci
        self.ResPartner = self.erp.ResPartner
        self.Investment = self.erp.GenerationkwhInvestment
        self.Investment.dropAll()
        self.MailMockup = self.erp.GenerationkwhMailmockup
        self.MailMockup.activate()

    def tearDown(self):
        self.MailMockup.deactivate()
        self.erp.rollback()
        self.erp.close()

    def list(self, partner_id):
        return self.ResPartner.www_generationkwh_investments(partner_id)


    def test_investments(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        name = self.Investment.read(id, ['name'])['name']

        result = self.list(partner_id=self.personalData.partnerid)
        self.assertNsEqual(ns(data=result), u"""\
            data:
            - name: {investment_name}
              id: {id}
              member_id:
              - {member_id}
              - {surname}, {name}
              order_date: '2017-01-01'
              purchase_date: false
              first_effective_date: false
              last_effective_date: false
              draft: true
              active: true
              nshares: 40
              nominal_amount: 4000.0
              amortized_amount: 0.0
            """.format(
                id = id,
                investment_name=name,
                **self.personalData
            ))

    def test_investments_not_member(self):
        partner_id=self.erp.ResPartner.search([('vat','=','ES'+self.personalData.nonMemberNif)])[0]
        result = self.list(partner_id=partner_id)
        self.assertNsEqual(ns(data=result), """\
            data: []
            """)



@unittest.skipIf(not dbconfig, "depends on ERP")
class PartnerAssignments_Test(unittest.TestCase):

    from generationkwh.testutils import assertNsEqual

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Soci = self.erp.SomenergiaSoci
        self.ResPartner = self.erp.ResPartner
        self.Investment = self.erp.GenerationkwhInvestment
        self.Investment.dropAll()
        self.Assignment = self.erp.GenerationkwhAssignment
        self.Contract = self.erp.GiscedataPolissa
        self.Cups = self.erp.GiscedataCupsPs
        self.Assignment.dropAll()

        self.contract_id = 400
        self.contract_id2 = 401

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    def list(self, partner_id):
        return self.ResPartner.www_generationkwh_assignments(partner_id)

    def test_assignments_whenNotAMember(self):
        partner_id=self.erp.ResPartner.search([('vat','=','ES'+self.personalData.nonMemberNif)])[0]
        result = self.list(partner_id=partner_id)
        self.assertNsEqual(ns(data=result), """\
            data: []
            """)

    def test_assignments_none(self):
        result = self.list(partner_id=self.personalData.partnerid)
        self.assertNsEqual(ns(data=result), """\
            data: []
            """)

    def contractInfo(self, contract_id):
        contract = ns(self.Contract.read(contract_id,[
            'name',
            'data_ultima_lectura',
            'state',
            'cups',
            'cups_direccio',
            'tarifa'
            ]))
        cups = self.Cups.read(contract.cups[0], ['conany_kwh'])
        contract.annualUseKwh = cups['conany_kwh']
        return contract

    def test_assignments_single(self):

        id = self.Assignment.create(dict(
            contract_id=self.contract_id,
            member_id=self.personalData.member_id,
            priority=1,
            )).id

        contract = self.contractInfo(self.contract_id)

        result = self.list(partner_id=self.personalData.partnerid)
        self.assertNsEqual(ns(data=result), u"""\
            data:
            - id: {id}
              priority: 1
              member_id: {member_id}
              member_name: {surname}, {name}
              contract_id: {contract_id}
              contract_name: '{contract.name}'
              contract_last_invoiced: '{contract.data_ultima_lectura}'
              contract_state: {contract.state}
              annual_use_kwh: {contract.annualUseKwh}
              contract_address: {contract.cups_direccio}
              contract_tariff: {contract.tarifa}
            """.format(**dict(
                self.personalData,
                id=id,
                contract_id=self.contract_id,
                contract=contract,
            )))

    def test_assignments_expired(self):

        id = self.Assignment.create(dict(
            contract_id=self.contract_id,
            member_id=self.personalData.member_id,
            priority=1,
            )).id

        contract = self.contractInfo(self.contract_id)

        self.Assignment.expire(self.contract_id, self.personalData.member_id)

        result = self.list(partner_id=self.personalData.partnerid)
        self.assertNsEqual(ns(data=result), """\
            data: []
            """)

    def test_assignments_many(self):

        id = self.Assignment.create(dict(
            contract_id=self.contract_id,
            member_id=self.personalData.member_id,
            priority=1,
            )).id

        contract = self.contractInfo(self.contract_id)

        id2 = self.Assignment.create(dict(
            contract_id=self.contract_id2,
            member_id=self.personalData.member_id,
            priority=0,
            )).id

        contract2 = self.contractInfo(self.contract_id2)


        result = self.list(partner_id=self.personalData.partnerid)
        self.assertNsEqual(ns(data=result), u"""\
            data:
            - id: {id2}
              priority: 0
              member_id: {member_id}
              member_name: {surname}, {name}
              contract_id: {contract_id2}
              contract_name: '{contract2.name}'
              contract_last_invoiced: '{contract2.data_ultima_lectura}'
              contract_state: {contract2.state}
              annual_use_kwh: {contract2.annualUseKwh}
              contract_address: {contract2.cups_direccio}
              contract_tariff: {contract2.tarifa}
            - id: {id}
              priority: 1
              member_id: {member_id}
              member_name: {surname}, {name}
              contract_id: {contract_id}
              contract_name: '{contract.name}'
              contract_last_invoiced: '{contract.data_ultima_lectura}'
              contract_state: {contract.state}
              annual_use_kwh: {contract.annualUseKwh}
              contract_address: {contract.cups_direccio}
              contract_tariff: {contract.tarifa}
            """.format(**dict(
                self.personalData,
                id=id,
                contract_id=self.contract_id,
                contract=contract,
                id2=id2,
                contract_id2=self.contract_id2,
                contract2=contract2,
            )))



if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
