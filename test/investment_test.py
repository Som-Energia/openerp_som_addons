#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from yamlns import namespace as ns
import erppeek_wst
import generationkwh.investmentmodel as gkwh
from generationkwh.testutils import assertNsEqual


@unittest.skipIf(not dbconfig, "depends on ERP")
class Investment_OLD_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Soci = self.erp.SomenergiaSoci
        self.Investment = self.erp.GenerationkwhInvestment
        self.Investment.dropAll()

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    assertNsEqual=assertNsEqual

    #TODO: move this in a utils class (copy pasted from Investment_Amortization_Test
    def assertLogEquals(self, log, expected):
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )

        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)

    def test__effective_investments_tuple__noInvestments(self):
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [])

    def test__create_from_accounting__all(self):
        # Should fail whenever Gijsbert makes further investments
        # Update: We add the fiscal year closing investments

        self.Investment.create_from_accounting(1, None, None, 0, None)

        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
                [1, '2017-09-21', False, -1],
                [1, '2017-09-26', False, -1],
                [1, '2017-09-28', False, -1],
                [1, '2017-12-01', False, -2],
                [1, '2017-12-01', False, -2],
                [1, '2018-08-24', False, -1],
                [1, '2018-08-24', False, -1],
                [1, '2018-08-24', False, -1],
                [1, '2019-01-25', False, -2],
                [1, '2019-01-25', False, -2],
                [1, '2019-07-11', False, -1],
                [1, '2019-07-11', False, -1],
                [1, '2019-08-06', False, -1],
                [1, '2019-12-03', False, -2],
                [1, '2019-12-03', False, -2],
            ])

    def test__create_from_accounting__restrictingFirst(self):
        self.Investment.create_from_accounting(1, '2015-07-01', '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__seesUnactivePartner(self):

        self.Soci.write(1, dict(active=False))
        self.Investment.create_from_accounting(1, '2015-07-01', '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__restrictingLast(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__noWaitingDays(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, False, False,  1],
                [1, False, False, 30],
                [1, False, False, 30],
            ])

    def test__create_from_accounting__nonZeroWaitingDays(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 1, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', False, 15],
                [1, '2015-07-01', False, 10],
                [1, '2015-07-30', False,  1],
                [1, '2015-11-21', False, 30],
                [1, '2015-11-21', False, 30],
            ])

    def test__create_from_accounting__nonZeroExpireYears(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 1, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-07-30', '2017-07-30',  1],
                [1, '2015-11-21', '2017-11-21', 30],
                [1, '2015-11-21', '2017-11-21', 30],
            ])

    def test__create_from_accounting__severalMembers(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investment.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
                [38, '2015-06-30', False, 3],
                [38, '2015-10-13', False, 1],
                [38, '2015-10-20', False, -1],
            ])

    def test__create_from_accounting__severalMembersArray_reorderbyPurchase(self):
        self.Investment.create_from_accounting([1,38], None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [38, '2015-06-30', False, 3],
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [38, '2015-10-13', False, 1],
                [38, '2015-10-20', False, -1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__create_from_accounting__noMemberTakesAll(self):
        self.Investment.create_from_accounting(None, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])
        self.assertEqual(
            self.Investment.effective_investments_tuple(38, None, None),
            [
                [38, '2015-06-30', False, 3],
            ])

    def test__create_from_accounting__ignoresExisting(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.Investment.create_from_accounting(1, None, '2015-07-29', 0, None)
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', '2017-11-20', 30],
                [1, '2015-11-20', '2017-11-20', 30],
            ])

    def test__effective_investments_tuple__filtersByMember(self):
        self.Investment.create_from_accounting(1, None, '2015-11-20', 0, None)
        self.Investment.create_from_accounting(38, None, '2015-11-20', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(1, None, None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
                [1, '2015-07-29', False,  1],
                [1, '2015-11-20', False, 30],
                [1, '2015-11-20', False, 30],
            ])

    def test__effective_investments_tuple__filtersByFirst_removesUnstarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-07-20', None),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByFirst_keepsUnexpiredWhicheverTheDate(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '4017-07-20', None),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByFirst_passesNotYetExpired(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-06-30', None),
            [
                [1, '2015-06-30', '2017-06-30', 15],
                [1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByFirst_removesExpired(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, 2)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, '2017-07-01', None),
            [
                #[1, '2015-06-30', '2017-06-30', 15],
                #[1, '2015-06-30', '2017-06-30', 10],

            ])

    def test__effective_investments_tuple__filtersByLast_removesUnstarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', None, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-11-19'),
            [
                #[1, False, False, 15], # Unstarted
                #[1, False, False, 10], # Unstarted
            ])

    def test__effective_investments_tuple__filtersByLast_includesStarted(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-06-30'),
            [
                [1, '2015-06-30', False, 15],
                [1, '2015-06-30', False, 10],
            ])

    def test__effective_investments_tuple__filtersByLast_excludesStartedLater(self):
        self.Investment.create_from_accounting(1, None, '2015-06-30', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, '2015-06-29'),
            [
                #[1, '2015-06-30', False, 15], # Not yet started
                #[1, '2015-06-30', False, 10], # Not yet started
            ])

    def test__effective_investments_tuple__deactivatedNotShown(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investment.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investment.deactivate(toBeDeactivated)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # deactivated
                [1, '2015-07-29', False,  1],
            ])

    def test__create_from_accounting__unactiveNotRecreated(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        toBeDeactivated=self.Investment.search([
            ('member_id','=',1),
            ('nshares','=',10),
            ])[0]
        self.Investment.deactivate(toBeDeactivated)
        self.Investment.create_from_accounting(1, None, '2015-11-19', 0, None)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-06-30', False, 15],
                #[1, '2015-06-30', False, 10], # still deactivated
                [1, '2015-07-29', False,  1],
            ])

    def test__set_effective__wait(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, None, 1, None, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', False, 15],
                [1, '2015-07-01', False, 10],
                [1, '2015-07-30', False,  1],
            ])

    def test__set_effective__waitAndExpire(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, None, 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-07-30', '2017-07-30',  1],
            ])

    def test__set_effective__purchasedEarlierIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective('2015-07-01', None, 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, False, False, 15],
                [1, False, False, 10],
                [1, '2015-07-30', '2017-07-30',  1],
            ])

    def test__set_effective__purchasedLaterIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, False, False,  1],
            ])

    def test__set_effective__alreadySetIgnored(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.Investment.set_effective(None, None, 10, 4, False)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-01', '2017-07-01', 15],
                [1, '2015-07-01', '2017-07-01', 10],
                [1, '2015-08-08', '2019-08-08',  1],
            ])

    def test__set_effective__alreadySetForced(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        self.Investment.set_effective(None, '2015-06-30', 1, 2, False)
        self.Investment.set_effective(None, None, 10, 4, True)
        self.assertEqual(
            self.Investment.effective_investments_tuple(None, None, None),
            [
                [1, '2015-07-10', '2019-07-10', 15],
                [1, '2015-07-10', '2019-07-10', 10],
                [1, '2015-08-08', '2019-08-08',  1],
            ])

    # TODO: extent to move expire

    def test__member_has_effective__noInvestments(self):
        self.assertFalse(
            self.Investment.member_has_effective(None, None, None))

    def test__member_has_effective__insideDates(self):
        self.Investment.create_from_accounting(1,'2010-01-01', '2015-07-03',
            1, None)
        self.assertTrue(
            self.Investment.member_has_effective(1,'2015-07-01','2015-07-01'))

@unittest.skipIf(not dbconfig, "depends on ERP")
class Investment_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Invoice = self.erp.AccountInvoice
        self.InvoiceLine = self.erp.AccountInvoiceLine
        self.Partner = self.erp.ResPartner
        self.Investment = self.erp.GenerationkwhInvestment
        self.PaymentLine = self.erp.PaymentLine
        self.PaymentMandate = self.erp.PaymentMandate
        self.ResPartnerAddress = self.erp.ResPartnerAddress
        self.ResPartner = self.erp.ResPartner
        self.AccountMove = self.erp.AccountMove
        self.AccountPeriod = self.erp.AccountPeriod
        self.MailMockup = self.erp.GenerationkwhMailmockup
        self.MailMockup.activate()

    def tearDown(self):
        self.MailMockup.deactivate()
        self.erp.rollback()
        self.erp.close()

    assertNsEqual=assertNsEqual

    #Copied to tests/investment_test.py
    def assertLogEquals(self, log, expected):
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )

        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)

    #Copied to tests/investment_test.py
    def assertMailLogEqual(self, expected):
        self.assertNsEqual(self.MailMockup.log() or '{}', expected)

    @unittest.skip('Not implemented')
    def test__create_from_form__whenBadOrderDate(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            'baddate', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertFalse(id) # ??

    def test__mark_as_invoiced(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_signed(id, '2017-01-03')
        self.Investment.mark_as_invoiced(id)

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log') # TODO: Test
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")

        self.assertLogEquals(log,
            u'INVOICED: Facturada i remesada\n'
            u'SIGN: Inversió signada amb data 2017-01-03\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.123,'
            u' Quantitat: 4000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: false
            first_effective_date: false
            last_effective_date: false
            nshares: 40
            amortized_amount: 0.0
            move_line_id: false
            active: true
            draft: false
            signed_date: '2017-01-03'
            """.format(
                id=id,
                **self.personalData
                ))

    # TODO: mark_as_invoiced twice

    def test__mark_as_paid__singleInvestment(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_signed(id, '2017-01-03')
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log') # TODO: Test
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")

        self.assertLogEquals(log,
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'SIGN: Inversió signada amb data 2017-01-03\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.123,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-03' # Changed!
            first_effective_date: '2018-01-03'
            last_effective_date: '2042-01-03'
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: true
            draft: false
            signed_date: '2017-01-03'
            """.format(
                id=id,
                **self.personalData
                ))

    def test__mark_as_paid__samePurchaseDateSetToAll(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_invoiced(id1)
        self.Investment.mark_as_invoiced(id2)
        self.Investment.mark_as_paid([id1,id2], '2017-01-03')

        result = self.Investment.read(
            [id1,id2],
            ['purchase_date'],
            order='id')

        self.assertNsEqual(ns(data=result), """\
            data:
            - purchase_date: '2017-01-03'
              id: {id1}
            - purchase_date: '2017-01-03'
              id: {id2}
            """.format(id1=id1, id2=id2))

    def test__mark_as_paid__oldLogKept(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02', # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_invoiced(id1)
        self.Investment.mark_as_invoiced(id2)
        self.Investment.mark_as_paid([id1,id2], '2017-01-03')

        result = self.Investment.read([id1,id2], ['log'], order='id')

        self.assertLogEquals(result[0]['log'],
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.1,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertLogEquals(result[1]['log'],
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.2,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__mark_as_paid__alreadyPaid(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        with self.assertRaises(Exception) as ctx:
            self.Investment.mark_as_paid([id], '2017-01-03')

        self.assertEqual(ctx.exception.faultCode,
            "Already paid"
            )

        result = self.Investment.read(id, ['log'])

        self.assertLogEquals(result['log'],
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.1,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__mark_as_unpaid__singleInvestment(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        self.Investment.mark_as_signed(id, '2017-01-03')
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        self.Investment.mark_as_unpaid([id])

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log') # TODO: Test
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")

        self.assertLogEquals(log,
            u'UNPAID: Devolució del pagament de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'SIGN: Inversió signada amb data 2017-01-03\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.123,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: false # Changed!
            first_effective_date: false
            last_effective_date: false
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: true
            draft: false
            signed_date: '2017-01-03'
            """.format(
            id=id,
            **self.personalData
        ))

    def test__mark_as_unpaid__manyInvestments(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )

        self.Investment.mark_as_invoiced(id1)
        self.Investment.mark_as_invoiced(id2)
        self.Investment.mark_as_paid([id1, id2], '2017-01-03')

        self.Investment.mark_as_unpaid([id1, id2])

        result = self.Investment.read(
            [id1, id2],
            ['purchase_date'],
            order='id')

        self.assertNsEqual(ns(data=result), """\
            data:
            - purchase_date: false
              id: {id1}
            - purchase_date: false
              id: {id2}
            """.format(id1=id1, id2=id2))

    def test__mark_as_unpaid__oldLogKept(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )

        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02',  # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
        )

        self.Investment.mark_as_invoiced(id1)
        self.Investment.mark_as_invoiced(id2)
        self.Investment.mark_as_paid([id1, id2], '2017-01-03')
        self.Investment.mark_as_unpaid([id1, id2])

        result = self.Investment.read([id1, id2], ['log'], order='id')

        self.assertLogEquals(result[0]['log'],
            u'UNPAID: Devoluci\xf3 del pagament de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.1,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertLogEquals(result[1]['log'],
            u'UNPAID: Devoluci\xf3 del pagament de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.2,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__mark_as_unpaid__notPaid(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        self.Investment.mark_as_invoiced(id)
        with self.assertRaises(Exception) as ctx:
            self.Investment.mark_as_unpaid([id])
        self.assertEqual(ctx.exception.faultCode,
            "No pending amount to unpay")

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')

        self.assertLogEquals(log,
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.123,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__mark_as_unpaid__draft(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
        )
        with self.assertRaises(Exception) as ctx:
            self.Investment.mark_as_unpaid([id])
        self.assertEqual(ctx.exception.faultCode,
            "Not invoiced yet")

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')

        self.assertLogEquals(log,
            u'ORDER: Formulari omplert des de la IP 10.10.23.123,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def assertInvoiceInfoEqual(self, invoice_id, expected):
        def proccesLine(line):
            line = ns(line)
            line.product_id = line.product_id[1]
            line.account_id = line.account_id[1]
            line.uos_id = line.uos_id[1]
            line.note = ns.loads(line.note) if line.note else line.note
            del line.id
            return line

        invoice = ns(self.Invoice.read(invoice_id, [
            'amount_total',
            'amount_untaxed',
            'partner_id',
            'type',
            'name',
            'number',
            'journal_id',
            'account_id',
            'partner_bank',
            'payment_type',
            'date_invoice',
            'invoice_line',
            'check_total',
            'origin',
            'sii_to_send',
            'mandate_id',
            'state',
        ]))
        invoice.journal_id = invoice.journal_id[1]
        invoice.mandate_id = invoice.mandate_id and invoice.mandate_id[0]
        invoice.partner_bank = invoice.partner_bank[1] if invoice.partner_bank else "None"
        invoice.account_id = invoice.account_id[1]
        invoice.invoice_line = [
            proccesLine(line)
            for line in self.InvoiceLine.read(invoice.invoice_line, [])
            ]
        self.assertNsEqual(invoice, expected)

    def test__create_amortization_invoice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24, 7)
        self.assertTrue(invoice_id)

        investment = self.Investment.browse(id)

        self.assertInvoiceInfoEqual(invoice_id, u"""\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 73.0
            amount_untaxed: 73.0
            check_total: 73.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500000000 {p.surname}, {p.name}
              name: 'Amortització fins a 30/01/2018 de {investment_name} '
              invoice_id:
              - {id}
              - 'SI: {investment_name}'
              price_unit: 80.0
              price_subtotal: 80.0
              invoice_line_tax_id: []
              note:
                pendingCapital: 1920.0
                amortizationDate: '2018-01-30'
                amortizationNumber: 1
                amortizationTotalNumber: 24
                investmentId: {investment_id}
                investmentName: {investment_name}
                investmentPurchaseDate: '2017-01-03'
                investmentLastEffectiveDate: '2042-01-03'
                investmentInitialAmount: 2000
              discount: 0.0
              account_analytic_id: false
              quantity: 1.0
              product_id: '[GENKWH_AMOR] Amortització Generation kWh'
            - account_analytic_id: false
              account_id: 475119000001 IRPF 19% GENERATION KWh
              discount: 0.0
              invoice_id:
              - {id}
              - 'SI: {investment_name}'
              invoice_line_tax_id: []
              name: 'Retenció IRPF sobre l''estalvi del Generationkwh de 2017 de {investment_name} '
              note:
                amortizationDate: '2018-01-30'
                amortizationNumber: 1
                amortizationTotalNumber: 24
                investmentId: {investment_id}
                investmentInitialAmount: 2000
                investmentLastEffectiveDate: '2042-01-03'
                investmentName: {investment_name}
                investmentPurchaseDate: '2017-01-03'
                pendingCapital: 1920.0
              origin: false
              price_subtotal: -7.0
              price_unit: -7.0
              product_id: '[GENKWH_IRPF] Retenció IRPF estalvi Generation kWh'
              quantity: 1.0
              uos_id: PCE
            journal_id: Factures GenerationkWh
            mandate_id: {mandate_id}
            name: {investment_name}-AMOR{year}
            number: {investment_name}-AMOR{year}
            origin: {investment_name}
            partner_bank: {iban}
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type:
            - 2
            - Transferencia
            sii_to_send: false
            type: in_invoice
            state: draft
            """.format(
                invoice_date = datetime.today().strftime("%Y-%m-%d"),
                id = invoice_id,
                iban = 'ES77 1234 1234 1612 3456 7890',
                year = 2018,
                investment_name = investment.name,
                p = self.personalData,
                investment_id = id,
                mandate_id = False,
            ))

    def test__create_amortization_invoice__twice(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        inv = self.Investment.read(id, ['name'])

        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24, 7)

        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24, 7)

        self.assertEqual(errors,
            u"Inversió {id}: L'amortització {name}-AMOR2018 ja existeix"
            .format(**inv))

    def test__create_amortization_invoice__errorWhenNoBank(self):
        #TODO: especificar l'excepció
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Partner.write(self.personalData.partnerid,dict(bank_inversions = False))

        invocie_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30' , 80, 1, 24, 7)

        self.assertEqual(unicode(errors),
            u"Inversió {id}: El partner {surname}, {name} no té informat un compte corrent\n"
            .format(id=id, **dbconfig.personaldata))

    def test__create_amortization_invoice__withUnnamedInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2016-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        self.Investment.write(id, dict(
            name=None)
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2016-01-03')

        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-03', 80, 1, 24, 7)

        invoice = self.Invoice.browse(invoice_id)
        self.assertEqual(invoice.name,
            "GENKWHID{}-AMOR2018".format(id))

    def test__amortization_invoice_report(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000, # amount_in_euros
            '10.10.23.1', # ip
            'ES7712341234161234567890', # iban
            )

        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24, 7)

        inv = ns(self.Investment.read(id, [
            'name',
        ]))

        result = self.Invoice.investmentAmortization_notificationData_asDict([invoice_id])
        self.assertNsEqual(ns(result), u"""\
            inversionName: {inv.name}
            ownerName: {surname}, {name}
            ownerNif: {nif}
            receiptDate: '{today}'
            inversionInitialAmount: 2.000,00
            inversionPendingCapital: 1.920,00
            inversionPurchaseDate: '03/01/2017'
            inversionExpirationDate: '03/01/2042'
            amortizationAmount: 73,00
            amortizationName: {inv.name}-AMOR2018
            amortizationTotalPayments: 24
            inversionBankAccount: ES77 1234 1234 1612 3456 7890
            amortizationDate: '30/01/2018'
            amortizationNumPayment: 1
            """.format(
                today = datetime.today().strftime("%d/%m/%Y"),
                nif = self.personalData.nif,
                name = self.personalData.name,
                surname = self.personalData.surname,
                inv = inv,
        ))


    def test__amortize__writes_log(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )
        self.Investment.mark_as_invoiced(investment_id)
        self.Investment.mark_as_paid([investment_id], '2000-01-05')
        self.Investment.amortize('2002-01-06', [investment_id])

        investment = self.Investment.read(investment_id, ['log'])
        self.assertLogEquals(investment['log'],
            u'AMORTIZATION: Generada amortització de 80.00 € pel 2002-01-05\n'
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.1,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__amortize__writesLogTwiceSameInvestment(self):
        investment_id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )
        self.Investment.mark_as_invoiced(investment_id)
        self.Investment.mark_as_paid([investment_id], '2000-01-05')
        self.Investment.amortize('2003-01-06', [investment_id])

        investment = self.Investment.read(investment_id, ['log'])
        self.assertLogEquals(investment['log'],
            u'AMORTIZATION: Generada amortització de 80.00 € pel 2003-01-05\n'
            u'AMORTIZATION: Generada amortització de 80.00 € pel 2002-01-05\n'
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.1,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

    def test__open_invoices__amortizationAllOk(self):

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )

        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice_id, errors = self.Investment.create_amortization_invoice(
            id, '2018-01-30', 80, 1, 24, 7)
        self.assertTrue(invoice_id)

        self.Investment.open_invoices([invoice_id])

        date_due_dt = datetime.today() + timedelta(7)
        date_due = date_due_dt.strftime('%Y-%m-%d')
        invoices_changes = self.Invoice.read(invoice_id,
            ['state',
             'date_due',
             ])

        self.assertEqual(invoices_changes, dict(
            id = invoice_id,
            state = 'open',
            date_due = date_due,
            ))

    def test__open_invoices__multipleInvoices(self):

        id1 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            1000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )
        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01',  # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
        )
        ids = [id1,id2]

        invoice_ids,errs = self.Investment.create_initial_invoices(ids)

        self.Investment.open_invoices(invoice_ids)

        date_due_dt = datetime.today() + timedelta(7)
        date_due = date_due_dt.strftime('%Y-%m-%d')
        invoices_changes = self.Invoice.read(invoice_ids,
            ['state',
             'date_due',
             ],
            order='id')

        self.assertEqual(invoices_changes, [dict(
            id = invoice_ids[0],
            state = 'open',
            date_due = date_due,
            ), dict(
            id=invoice_ids[1],
            state='open',
            date_due=date_due,
        )])


    def test__invoices_to_payment_order(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        invoice_ids, errs =  self.Investment.create_initial_invoices([id])
        self.Investment.open_invoices(invoice_ids)
        self.Investment.invoices_to_payment_order(invoice_ids, gkwh.investmentPaymentMode)
        invoice = self.Invoice.browse(invoice_ids[0])

        order_id = self.Investment.get_or_create_open_payment_order(gkwh.investmentPaymentMode)
        lines = self.PaymentLine.search([
            ('order_id','=', order_id),
            ('communication','like', invoice.origin),
            ])

        self.assertTrue(lines)

    def test__invoices_to_payment_order__multiple(self):

        ids=[]
        ids.append(self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.1',
            'ES7712341234161234567890',
            ))
        ids.append(self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-02',  # order_date
            2000,
            '10.10.23.2',
            'ES7712341234161234567890',
        ))

        invoice_ids, err =  self.Investment.create_initial_invoices(ids)
        self.Investment.open_invoices(invoice_ids)

        self.Investment.invoices_to_payment_order(invoice_ids, gkwh.investmentPaymentMode)


        # TODO: Take the origin from investment name
        invoices = self.Invoice.browse(invoice_ids)
        order_id = self.Investment.get_or_create_open_payment_order(gkwh.investmentPaymentMode)
        lines = [self.PaymentLine.search([
            ('order_id','=', order_id),
            ('communication','like', invoices[0].origin),
            ])]
        lines.append(self.PaymentLine.search([
            ('order_id','=', order_id),
            ('communication','like', invoices[1].origin),
            ]))
        self.assertEqual(len(invoice_ids), len(lines))

    def test__get_or_create_payment_mandate__calledTwiceReturnsSame(self):
        iban = 'ES8901825726580208779553'
        purpose = 'GENERATION kWh'
        creditor_code = 'CREDITORCODE'
        mandate1_id = self.Investment.get_or_create_payment_mandate(
            self.personalData.partnerid, iban, purpose, creditor_code)
        mandate2_id = self.Investment.get_or_create_payment_mandate(
            self.personalData.partnerid, iban, purpose, creditor_code)
        self.assertEqual(mandate1_id, mandate2_id)

    def test__get_or_create_payment_mandate__notOpenCreatsANewOne(self):
            iban = 'ES8901825726580208779553'
            purpose = 'GENERATION kWh'
            creditor_code = 'CREDITORCODE'
            mandate1_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)
            self.PaymentMandate.write(mandate1_id, dict(date_end='2015-01-01'))
            mandate2_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)
            self.assertNotEqual(mandate1_id, mandate2_id)

    def test__get_or_create_payment_mandate__newlyCreatedHasProperFields(self):
            iban = 'ES8901825726580208779553'
            purpose = 'GENERATION kWh'
            creditor_code = 'CREDITORCODE'

            old_mandate_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)
            # Ensure the next is new
            self.PaymentMandate.write(old_mandate_id, dict(date_end='2015-01-01'))

            mandate_id = self.Investment.get_or_create_payment_mandate(
                self.personalData.partnerid, iban, purpose, creditor_code)

            mandate = ns(self.PaymentMandate.read(mandate_id, []))
            self.assertTrue(mandate.name and
                all(x in 'abdcdef1234567890' for x in mandate.name),
                "mandate.name should be a lowercase hex code")
            mandate.creditor_id = mandate.creditor_id[1]
            partner = self.ResPartner.browse(self.personalData.partnerid)
            nom_complet = self.personalData.surname + ", " + self.personalData.name
            self.assertNsEqual(mandate, u"""\
                creditor_address: CL. Riu Güell, 68  17005 GIRONA (ESPAÑA)
                creditor_code: CREDITORCODE
                creditor_id: SOM ENERGIA SCCL
                date: '{today}'
                date_end: false
                debtor_address: {address}
                debtor_country: '67'
                debtor_iban: {iban}
                debtor_iban_print: {format_iban}
                debtor_name: {debtor_name}
                debtor_state: {state}
                debtor_vat: {vat}
                id: {id}
                mandate_scheme: core
                name: {name}
                notes: GENERATION kWh
                payment_type: recurring
                reference: res.partner,{partner_id}
                signed: true
                """.format(
                    id=mandate_id,
                    name=mandate.name, # always change
                    partner_id=self.personalData.partnerid,
                    vat="ES"+self.personalData.nif,
                    debtor_name=nom_complet,
                    address = partner.address[0].nv,
                    state = partner.address[0].state_id.name,
                    iban=iban,
                    format_iban=' '.join(
                        iban[n:n+4] for n in xrange(0,len(iban),4)),
                    today=datetime.today().strftime("%Y-%m-%d"),
                ))

    #Copied to tests/investment_test.py
    def _generationMailAccount(self):
        PEAccounts = self.erp.PoweremailCore_accounts
        return PEAccounts.search([
           ('name','=','Generation kWh')
            ])[0]

    def test__mark_as_paid__sendsPaymentEmail(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.investment_payment([id])
        self.MailMockup.deactivate()
        self.MailMockup.activate()

        self.Investment.mark_as_paid([id], datetime.today().strftime('%Y-%m-%d'))

        self.assertMailLogEqual('{}')

    def test__mark_as_unpaid__skipsMailIfThereIsNoInvoice(self):
        # This behaviour is needed just for the other test
        # to work without emiting invoices (which are slow)
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id) # instead of investment_payment
        self.Investment.mark_as_paid([id], datetime.today().strftime('%Y-%m-%d'))
        self.MailMockup.deactivate()
        self.MailMockup.activate()

        self.Investment.mark_as_unpaid([id])

        self.assertMailLogEqual('{}')

    def test__mark_as_unpaid__sendsMail(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.investment_payment([id])
        self.Investment.mark_as_paid([id], datetime.today().strftime('%Y-%m-%d'))
        self.MailMockup.deactivate()
        self.MailMockup.activate()

        investmentName = self.Investment.read(id, ['name'])['name']
        invoiceName = investmentName + '-JUST'
        invoice_id = self.Invoice.search([
            ('name', '=', invoiceName)
        ])[0]

        self.Investment.mark_as_unpaid([id])

        self.assertMailLogEqual("""
            logs:
            - model: account.invoice
              id: {invoice_id}
              template: generationkwh_mail_impagament
              from_id: [ {account_id} ]
            """.format(
                invoice_id=invoice_id,
                account_id = self._generationMailAccount(),
            ))


    def test__amortize__sendsMails(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        date_due_dt = datetime.today() + relativedelta(years=+2)
        date_due = date_due_dt.strftime('%Y-%m-%d')
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], datetime.today().strftime('%Y-%m-%d'))
        self.MailMockup.deactivate()
        self.MailMockup.activate()

        amortization_ids, errors = self.Investment.amortize(date_due, [id])

        self.assertMailLogEqual("""\
            logs:
            - model: account.invoice
              id: {id}
              template: generationkwh_mail_amortitzacio
              from_id: [ {account_id} ]
            """.format(
                id=amortization_ids[0],
                account_id = self._generationMailAccount(),
            ))

    def test__amortized_amount__zeroByDefault(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2015-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2015-01-02')
        investment = self.Investment.read(id, ['amortized_amount'])
        self.assertEqual(0.0, investment['amortized_amount'])

    def test__amortize__justBeforeAmortization(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2015-01-02')
        self.Investment.amortize('2017-01-01',[id])
        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(0, investment['amortized_amount'])

    def test__amortize__justAtAmortizationDate(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2015-01-02')

        self.Investment.amortize('2017-01-02',[id])

        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(40, investment['amortized_amount'])

    def test__amortize__secondAmortization(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2015-11-20')
        self.Investment.amortize('2017-11-20',[id])
        self.Investment.amortize('2018-11-20',[id])

        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(80, investment['amortized_amount'])

    def test__amortize__afterFullAmortization(self):
        self.Investment.create_from_accounting(1, None, '2015-11-19', None, None)
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2015-11-20')

        invoice,errors = self.Investment.amortize('2040-11-20',[id])
        investment = self.Investment.read(id,['amortized_amount'])
        self.assertTrue(invoice)
        self.assertEqual(1000, investment['amortized_amount'])

        invoice,errors = self.Investment.amortize('2041-11-20',[id])
        self.assertFalse(invoice)
        investment = self.Investment.read(id,['amortized_amount'])
        self.assertEqual(1000, investment['amortized_amount'])

    # Amortizations
    def pendingAmortizationSummary(self, id, currentDate):
        return self.Investment.pending_amortization_summary(currentDate, [id])

    def test__pending_amortization_summary__draft(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.assertEqual([0, 0.0],
            self.pendingAmortizationSummary(id, '2017-11-20'))

    def test__pending_amortization_summary__unpaid(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.assertEqual([0, 0.0],
            self.pendingAmortizationSummary(id, '2017-11-20'))

    def test__pending_amortization_summary__manyAmortizationsSameInvestment(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.assertEqual([3,120.],
            self.pendingAmortizationSummary(id, '2004-01-04'))

    def test__pending_amortization_summary__withDueInvestments(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.assertEqual([1, 40],
            self.pendingAmortizationSummary(id, '2002-01-02'))

    def test__pending_amortization_summary__notDue(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.assertEqual([0,0.0],
            self.pendingAmortizationSummary(id, '2002-01-01'))

    def test__pending_amortization_summary__whenPartiallyAmortized(self):
        mid = self.personalData.member_id
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2000-01-02')
        self.Investment.amortize('2002-01-02',[id])
        self.assertEqual([1,40],
            self.pendingAmortizationSummary(id, '2003-01-02'))

    def test__cancel__ok(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )

        self.Investment.cancel([id])
        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log') # TODO: Test
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")

        self.assertLogEquals(log,
            u'CANCEL: La inversió ha estat cancel·lada\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.123,'
            u' Quantitat: 4000 €, IBAN: ES7712341234161234567890\n'
            )
        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: false
            first_effective_date: false
            last_effective_date: false
            nshares: 40
            amortized_amount: 0.0
            move_line_id: false
            active: false
            draft: true
            signed_date: false
            """.format(
                id=id,
                **self.personalData
                ))


    def test__cancel__twice(self):
        with self.assertRaises(Exception) as ctx:
            id = self.Investment.create_from_form(
                self.personalData.partnerid,
                '2017-01-01', # order_date
                4000,
                '10.10.23.123',
                'ES7712341234161234567890',
                )

            self.Investment.cancel([id])
            self.Investment.cancel([id])

        self.assertEqual(ctx.exception.faultCode,
            "Inactive investments can not be cancelled"
            )

    def test__cancel__paid(self):
        with self.assertRaises(Exception) as ctx:
            id = self.Investment.create_from_form(
                self.personalData.partnerid,
                '2000-01-01',  # order_date
                2000,
                '10.10.23.1',
                'ES7712341234161234567890',
            )
            self.Investment.mark_as_invoiced(id)
            self.Investment.mark_as_paid([id], '2000-01-05')
            self.Investment.cancel([id])

        self.assertEqual(ctx.exception.faultCode,
            "Only unpaid investments can be cancelled"
            )

    def test__cancel__unpaid(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )
        self.Investment.mark_as_signed(id, '2000-01-03')
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2000-01-05')
        self.Investment.mark_as_unpaid([id])
        self.Investment.cancel([id])

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log') # TODO: Test
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")

        self.assertLogEquals(log,
            u'CANCEL: La inversió ha estat cancel·lada\n'
            u'UNPAID: Devolució del pagament de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'SIGN: Inversió signada amb data 2000-01-03\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.1,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2000-01-01'
            purchase_date: false
            first_effective_date: false
            last_effective_date: false
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: false
            draft: false
            signed_date: '2000-01-03'
            """.format(
                id=id,
                **self.personalData
                ))

    def test__resign__unpaid(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2000-01-01',  # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
        )
        self.Investment.mark_as_signed(id, '2000-01-03')
        self.Investment.investment_payment([id])
        self.Investment.mark_as_paid([id], '2000-01-05')
        self.Investment.mark_as_unpaid([id])
        self.Investment.resign([id])

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log') # TODO: Test
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")

        self.assertLogEquals(log,
            u'CANCEL: La inversió ha estat cancel·lada\n'
            u'UNPAID: Devolució del pagament de 2000 € [None]\n'
            u'PAID: Pagament de 2000 € efectuat [None]\n'
            u'INVOICED: Facturada i remesada\n'
            u'SIGN: Inversió signada amb data 2000-01-03\n'
            u'ORDER: Formulari omplert des de la IP 10.10.23.1,'
            u' Quantitat: 2000 €, IBAN: ES7712341234161234567890\n'
            )

        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2000-01-01'
            purchase_date: False
            first_effective_date: False
            last_effective_date: False
            nshares: 20
            amortized_amount: 0.0
            move_line_id: false
            active: false
            draft: false
            signed_date: '2000-01-03'
            """.format(
                id=id,
                **self.personalData
                ))

    def test__resign__paid(self):
        with self.assertRaises(Exception) as ctx:
            id = self.Investment.create_from_form(
                self.personalData.partnerid,
                '2000-01-01',  # order_date
                2000,
                '10.10.23.1',
                'ES7712341234161234567890',
            )
            self.Investment.investment_payment([id])
            self.Investment.mark_as_paid([id], '2000-01-05')
            self.Investment.resign([id])

        self.assertEqual(ctx.exception.faultCode,
            "Only unpaid investments can be cancelled"
            )

    def test__resign__alreadyCancelled(self):
        with self.assertRaises(Exception) as ctx:
            id = self.Investment.create_from_form(
                self.personalData.partnerid,
                '2000-01-01',  # order_date
                2000,
                '10.10.23.1',
                'ES7712341234161234567890',
            )
            self.Investment.investment_payment([id])
            self.Investment.mark_as_paid([id], '2000-01-05')
            self.Investment.mark_as_unpaid([id])
            self.Investment.resign([id])
            self.Investment.resign([id])

        self.assertEqual(ctx.exception.faultCode,
            "Inactive investments can not be cancelled"
            )

    def test__resign__notInvoiced(self):
        with self.assertRaises(Exception) as ctx:
            id = self.Investment.create_from_form(
                self.personalData.partnerid,
                '2000-01-01',  # order_date
                2000,
                '10.10.23.1',
                'ES7712341234161234567890',
            )
            self.Investment.resign([id])

        self.assertEqual(ctx.exception.faultCode,
            "Inversion without initial invoice, cannot resign"
            )

    def test__create_resign_invoice__allOk(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        invoice_ids, errs =  self.Investment.create_initial_invoices([id])
        invoice_id, errors = self.Investment.create_resign_invoice(id)

        self.assertTrue(invoice_id)
        investment = self.Investment.browse(id)
        self.assertInvoiceInfoEqual(invoice_id, u"""\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 2000.0
            amount_untaxed: 2000.0
            check_total: 0.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500000000 {p.surname}, {p.name}
              name: 'Inversió {investment_name} '
              invoice_id:
              - {id}
              - 'CR: {investment_name}-RES'
              price_unit: 100.0
              price_subtotal: 2000.0
              invoice_line_tax_id: []
              note: false
              discount: 0.0
              account_analytic_id: false
              quantity: 20.0
              product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
            journal_id: Factures GenerationkWh
            mandate_id: {mandate_id}
            name: {investment_name}-RES
            number: {investment_name}-RES
            origin: {investment_name}
            partner_bank: None
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type: false
            sii_to_send: false
            type: out_refund
            state: draft
            """.format(
                invoice_date = datetime.today().strftime("%Y-%m-%d"),
                id = invoice_id,
                investment_name = investment.name,
                p = self.personalData,
                mandate_id = False,
            ))

    def test__pay_resign_invoice__createOpenAndPayOk(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        invoice_ids, errs =  self.Investment.create_initial_invoices([id])
        self.Investment.open_invoices(invoice_ids)
        invoice_id, errors = self.Investment.create_resign_invoice(id)
        self.Investment.open_invoices([invoice_id])
        self.Investment.pay_resign_invoice(invoice_id)

        self.assertTrue(invoice_id)
        investment = self.Investment.browse(id)
        self.assertInvoiceInfoEqual(invoice_id, u"""\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 2000.0
            amount_untaxed: 2000.0
            check_total: 0.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500000000 {p.surname}, {p.name}
              name: 'Inversió {investment_name} '
              invoice_id:
              - {id}
              - 'CR: {investment_name}-RES'
              price_unit: 100.0
              price_subtotal: 2000.0
              invoice_line_tax_id: []
              note: false
              discount: 0.0
              account_analytic_id: false
              quantity: 20.0
              product_id: '[GENKWH_AE] Accions Energètiques Generation kWh'
            journal_id: Factures GenerationkWh
            mandate_id: {mandate_id}
            name: {investment_name}-RES
            number: {investment_name}-RES
            origin: {investment_name}
            partner_bank: None
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type: false
            sii_to_send: false
            type: out_refund
            state: paid
            """.format(
                invoice_date = datetime.today().strftime("%Y-%m-%d"),
                id = invoice_id,
                investment_name = investment.name,
                p = self.personalData,
                mandate_id = False,
            ))

    def test__divest__beforeEffectivePeriod(self):
        divestment_date = date.today()
        effective_date = divestment_date + timedelta(days=1)
        payment_date = date(effective_date.year-1, effective_date.month, effective_date.day)
        order_date = payment_date - timedelta(days=1)

        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            str(order_date),
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_signed(id, str(order_date))
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], str(payment_date))

        invoice_ids, errors = self.Investment.divest([id], str(divestment_date))
        self.assertEqual([], errors)

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log') 
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")

        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '{order_date}'
            purchase_date: '{payment_date}'
            first_effective_date: '{effective_date}'
            last_effective_date: '{divestment_date}'
            nshares: 10
            amortized_amount: 1000.0
            move_line_id: false
            active: false
            draft: false
            signed_date: '{order_date}'
            """.format(
                id=id,
                divestment_date = divestment_date,
                payment_date = payment_date,
                order_date = order_date,
                effective_date = effective_date,
                **self.personalData
                ))

    def test__divest__inEffectivePeriod(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2015-09-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_signed(id, '2015-09-03')
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2015-09-01')
        date_today = str(date.today())

        self.Investment.divest([id])

        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log')
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")
        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2015-09-01'
            purchase_date: '2015-09-01'
            first_effective_date: '2016-08-01'
            last_effective_date: '{date_today}'
            nshares: 10
            amortized_amount: 1000.0
            move_line_id: false
            active: true
            draft: false
            signed_date: '2015-09-03'
            """.format(
                id=id,
                date_today = date_today,
                **self.personalData
                ))

    def test__divest__beforeReturnPaymentOrderPeriod(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        date_paid = date.today() - timedelta(days=20)
        self.Investment.mark_as_paid([id], str(date_paid))

        invoice_ids, errors = self.Investment.divest([id])

        investment = ns(self.Investment.read(id, []))
        name = investment.pop('name')
        response = ns(error = errors)
        self.assertNsEqual(response, """
            error:
            - '{name}: Too early to divest (< 30 days from purchase)'
            """.format(
                name = name,
                ))

    def test__divest__alreadyDivested(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        date_paid = date.today() - timedelta(days=160)
        self.Investment.mark_as_paid([id], str(date_paid))

        invoice_ids, errors = self.Investment.divest([id])
        invoice_ids2, errors2 = self.Investment.divest([id])

        investment = ns(self.Investment.read(id, []))
        name = investment.pop('name')
        response = ns(error = errors2)
        self.assertNsEqual(response, """
            error:
            - 'Inversió {id}: La desinversió {name}-DES ja existeix'
            """.format(
                name = name,
                id = id,
                ))

    def test__divest__invoiceAfterAmortization(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2015-09-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_signed(id, '2017-01-03')
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2015-09-01')
        date_today = str(date.today())
        self.Investment.amortize('2017-09-02',[id])

        invoice_ids, error = self.Investment.divest([id])

        invoice_id = invoice_ids[0]
        investment = ns(self.Investment.read(id, []))
        log = investment.pop('log')
        investment_name = investment.pop('name')
        actions_log = investment.pop('actions_log')
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")
        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2015-09-01'
            purchase_date: '2015-09-01'
            first_effective_date: '2016-08-01'
            last_effective_date: '{date_today}'
            nshares: 10
            amortized_amount: 1000.0
            move_line_id: false
            active: true
            draft: false
            signed_date: '2017-01-03'
            """.format(
                id=id,
                date_today = date_today,
                **self.personalData
                ))
        self.assertInvoiceInfoEqual(invoice_id, u"""\
            account_id: 410000{p.nsoci:0>6s} {p.surname}, {p.name}
            amount_total: 960.0
            amount_untaxed: 960.0
            check_total: 960.0
            date_invoice: '{invoice_date}'
            id: {id}
            invoice_line:
            - origin: false
              uos_id: PCE
              account_id: 163500000000 {p.surname}, {p.name}
              name: 'Desinversió total de {investment_name} a {invoice_date} '
              invoice_id:
              - {id}
              - 'SI: {investment_name}'
              price_unit: 960.0
              price_subtotal: 960.0
              invoice_line_tax_id: []
              note:
                pendingCapital: 0.0
                divestmentDate: '{invoice_date}'
                investmentId: {investment_id}
                investmentName: {investment_name}
                investmentPurchaseDate: '2015-09-01'
                investmentLastEffectiveDate: '2040-09-01'
                investmentInitialAmount: 1000
              discount: 0.0
              account_analytic_id: false
              quantity: 1.0
              product_id: '[GENKWH_AMOR] Amortització Generation kWh'
            journal_id: Factures GenerationkWh
            mandate_id: {mandate_id}
            name: {investment_name}-DES
            number: {investment_name}-DES
            origin: {investment_name}
            partner_bank: {iban}
            partner_id:
            - {p.partnerid}
            - {p.surname}, {p.name}
            payment_type:
            - 2
            - Transferencia
            sii_to_send: false
            type: in_invoice
            state: open
            """.format(
                invoice_date = datetime.today().strftime("%Y-%m-%d"),
                id = invoice_id,
                iban = 'ES77 1234 1234 1612 3456 7890',
                year = 2018,
                investment_name = investment_name,
                p = self.personalData,
                investment_id = id,
                mandate_id = False,
            ))

    def test__create_from_transfer__whenNotAMember(self):
        with self.assertRaises(Exception) as ctx:
            id = self.Investment.create_from_transfer(
                1436, # magic number, existing investment
                1, # magic number, not member
                '2017-01-01', # order_date
                'ES7712341234161234567890',
                )
        self.assertEqual(ctx.exception.faultCode,
            "Destination partner is not a member"
            )

    def test__create_from_transfer__whenInvestmentDraft(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )

        with self.assertRaises(Exception) as ctx:
            self.Investment.create_from_transfer(
                id, # magic number, existing investment
                1, # magic number, not member
                '2017-01-01', # order_date
                'ES7712341234161234567890',
                )
        self.assertEqual(ctx.exception.faultCode,
            "Investment in draft, so not transferible"
            )

    def test__create_from_transfer__whenInvestmentInactive(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.deactivate(id)

        with self.assertRaises(Exception) as ctx:
            self.Investment.create_from_transfer(
                id, # magic number, existing investment
                self.personalData.partnerid,
                '2017-01-26', # order_date
                'ES7712341234161234567890',
                )
        self.assertEqual(ctx.exception.faultCode,
            "Investment not active"
            )

    def test__create_from_transfer__whenFullAmortized(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)

        self.Investment.mark_as_paid([id], '2017-01-03')
        invoice,errors = self.Investment.amortize('2042-11-20',[id])

        with self.assertRaises(Exception) as ctx:
            self.Investment.create_from_transfer(
                id,
                self.personalData.partnerid,
                '2017-01-26', # order_date
                'ES7712341234161234567890',
                )
        self.assertEqual(ctx.exception.faultCode,
            "Amount to return = 0, not transferible"
            )

    def getAMember(self):
        return ns(self.erp.SomenergiaSoci.read(1))

    def test__create_from_transfer__allOk(self):
        newMember = self.getAMember()

        old_id = self.Investment.create_from_form(
            newMember.partner_id[0],
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_signed(old_id, '2017-01-03')
        self.Investment.mark_as_invoiced(old_id)
        self.Investment.mark_as_paid([old_id], '2017-01-02')
        date_today = str(date.today())

        new_investment_id = self.Investment.create_from_transfer(
            old_id,
            self.personalData.partnerid,
            '2019-05-01',
            'ES7712341234161234567890',
            )

        old_investment = ns(self.Investment.read(old_id, []))
        log = old_investment.pop('log')
        name = old_investment.pop('name')
        actions_log = old_investment.pop('actions_log')
        id_emission, name_emission = old_investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")
        self.assertNsEqual(old_investment, u"""
            id: {id}
            member_id:
            - {newMember.id}
            - {newMember.name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-02'
            first_effective_date: '2018-01-02'
            last_effective_date: '2019-05-01'
            nshares: 10
            amortized_amount: 1000.0
            move_line_id: false
            active: true
            draft: false
            signed_date: '2017-01-03'
            """.format(
                id=old_id,
                newMember = newMember,
                **self.personalData
                ))

        investment = ns(self.Investment.read(new_investment_id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log')
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")
        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-02'
            first_effective_date: '2019-05-02'
            last_effective_date: '2042-01-02'
            nshares: 10
            amortized_amount: 0.0
            move_line_id: false
            active: true
            draft: false
            signed_date: false
            """.format(
                id=new_investment_id,
                **self.personalData
                ))

    def test__create_from_transfer__partialAmortizedAllOk(self):
        newMember = self.getAMember()
        id = self.Investment.create_from_form(
            newMember.partner_id[0],
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_signed(id, '2017-01-03')
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-02')
        date_today = str(date.today())
        self.Investment.amortize('2019-04-30', [id])

        new_investment_id = self.Investment.create_from_transfer(
            id,
            self.personalData.partnerid,
            '2019-05-01',
            'ES7712341234161234567890',
            )

        old_investment = ns(self.Investment.read(id, []))
        log = old_investment.pop('log')
        name = old_investment.pop('name')
        actions_log = old_investment.pop('actions_log')
        id_emission, name_emission = old_investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")
        self.assertNsEqual(old_investment, u"""
            id: {id}
            member_id:
            - {newMember.id}
            - {newMember.name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-02'
            first_effective_date: '2018-01-02'
            last_effective_date: '2019-05-01'
            nshares: 10
            amortized_amount: 1000.0
            move_line_id: false
            active: true
            draft: false
            signed_date: '2017-01-03'
            """.format(
                newMember = newMember,
                id=id,
                **self.personalData
                ))

        investment = ns(self.Investment.read(new_investment_id, []))
        log = investment.pop('log')
        name = investment.pop('name')
        actions_log = investment.pop('actions_log')
        id_emission, name_emission = investment.pop('emission_id')
        self.assertEqual(name_emission, "GenerationkWH")
        self.assertNsEqual(investment, u"""
            id: {id}
            member_id:
            - {member_id}
            - {surname}, {name}
            order_date: '2017-01-01'
            purchase_date: '2017-01-02'
            first_effective_date: '2019-05-02'
            last_effective_date: '2042-01-02'
            nshares: 10
            amortized_amount: 40.0
            move_line_id: false
            active: true
            draft: false
            signed_date: false
            """.format(
                id=new_investment_id,
                **self.personalData
                ))

    def test__move_line_when_tranfer__allOk(self):
        newMember = self.getAMember()
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-09-02')
        partner = self.ResPartner.browse(self.personalData.partnerid)

        move_id, moveline_debit, moveline_credit = self.Investment.move_line_when_tranfer(
            partner.id,
            newMember.partner_id,
            partner.property_account_gkwh.id,
            newMember.property_account_gkwh[0],
            1000,
            '2017-01-01'
            )

        period_name = datetime.today().strftime('%m/%Y')
        period_id = self.AccountPeriod.search([
            ('name', '=', period_name),
            ])[0]
        move = ns(self.AccountMove.read(move_id, []))
        self.assertNsEqual(move,u"""
            id: {move_id}
            amount: 1000.0
            journal_id:
            - 46
            - Factures GenerationkWh
            name: Transfer
            partner_id: false
            ref: '0000'
            state: posted
            to_check: false
            type: journal_voucher
            date: '{date}'
            period_id:
            - {period_id}
            - {period_name}
            line_id:
            - {moveline_credit}
            - {moveline_debit}
            """.format(
            date=datetime.today().strftime("%Y-%m-%d"),
            period_id= period_id,
            period_name = period_name,
            moveline_debit = moveline_debit,
            moveline_credit = moveline_credit,
            move_id = move_id,
            ))

    def test__get_dayshares_investmentyear__noDayShares(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        inv_obj = self.Investment.read(id)

        nDayShares = self.Investment.get_dayshares_investmentyear(inv_obj,'2017-01-01','2017-12-31')

        self.assertEqual(nDayShares, 0)

    def test__get_dayshares_investmentyear__ADaySharesOneCompleteInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        inv_obj = self.Investment.read(id)

        nDayShares = self.Investment.get_dayshares_investmentyear(inv_obj,'2019-01-09','2019-01-10')

        self.assertEqual(nDayShares, 20)

    def test__get_dayshares_investmentyear__someDaysSharesOneCompleteInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-03')
        inv_obj = self.Investment.read(id)

        nDayShares = self.Investment.get_dayshares_investmentyear(inv_obj,'2019-01-01','2020-01-01')

        self.assertEqual(nDayShares, 7300)

    def test__get_dayshares_investmentyear__someDaysSharesOneNoCompleteInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-03-01')
        inv_obj = self.Investment.read(id)

        nDayShares = self.Investment.get_dayshares_investmentyear(inv_obj,'2018-01-01','2019-01-01')

        self.assertEqual(nDayShares, 6120)

    def test__get_dayshares_investmentyear__someDaysSharesSomeCompletesInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-03-01')
        inv_obj = self.Investment.read(id)
        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2018-01-01', # order_date
            200,
            '10.10.23.1',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id2)
        self.Investment.mark_as_paid([id2], '2018-03-01')

        nDayShares = self.Investment.get_dayshares_investmentyear(inv_obj,'2019-01-01','2020-01-01')

        self.assertEqual(nDayShares, 7300)


    def test__is_last_year_amortized__True(self):
        newMember = self.getAMember()
        id = self.Investment.create_from_form(
            newMember.partner_id[0],
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-02')
        date_today = str(date.today())
        self.Investment.amortize('2019-04-30', [id])

        name = self.Investment.read(id, ['name'])['name']
        amortized = self.Investment.is_last_year_amortized(name, '2020')

        self.assertTrue(amortized)

    def test__is_last_year_amortized__False(self):
        newMember = self.getAMember()
        id = self.Investment.create_from_form(
            newMember.partner_id[0],
            '2017-01-01', # order_date
            1000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(id)
        self.Investment.mark_as_paid([id], '2017-01-02')
        date_today = str(date.today())

        name = self.Investment.read(id, ['name'])['name']
        amortized = self.Investment.is_last_year_amortized(name, '2020')

        self.assertFalse(amortized)

@unittest.skipIf(not dbconfig, "depends on ERP")
class InvestmentList_Test(unittest.TestCase):

    from generationkwh.testutils import assertNsEqual

    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Soci = self.erp.SomenergiaSoci
        self.Investment = self.erp.GenerationkwhInvestment
        self.AccountInvoice = self.erp.AccountInvoice
        self.PaymentLine = self.erp.PaymentLine
        self.Investment.dropAll()
        self.MailMockup = self.erp.GenerationkwhMailmockup
        self.MailMockup.activate()

    def tearDown(self):
        self.MailMockup.deactivate()
        self.erp.rollback()
        self.erp.close()

    def list(self, member_id):
        return self.Investment.list(member_id)

    def test_list_noInvestment(self):
        result = self.list(member_id=self.personalData.member_id)
        self.assertNsEqual(ns(data=result), dict(data=[]))

    def test_list_singleInvestment(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        name = self.Investment.read(id, ['name'])['name']

        result = self.list(member_id=self.personalData.member_id)
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
                investment_name = name,
                **self.personalData
            ))

    def test_list_manyInvestments(self):
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            2000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        id2 = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-02-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        name = self.Investment.read(id, ['name'])['name']
        name2 = self.Investment.read(id2, ['name'])['name']

        result = self.list(member_id=self.personalData.member_id)
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
              nshares: 20
              nominal_amount: 2000.0
              amortized_amount: 0.0
            - name: {investment_name2}
              id: {id2}
              member_id:
              - {member_id}
              - {surname}, {name}
              order_date: '2017-02-01'
              purchase_date: false
              first_effective_date: false
              last_effective_date: false
              draft: true
              active: true
              nshares: 40
              nominal_amount: 4000.0
              amortized_amount: 0.0
            """.format(
                investment_name=name,
                investment_name2=name2,
                id = id,
                id2 = id2,
                **self.personalData
            ))

    def test_list_otherInvestmentsIgnored(self):
        partner_nonInvestorAndMember = 2 # TODO: Fragile
        id = self.Investment.create_from_form(
            partner_nonInvestorAndMember,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        result = self.list(member_id=self.personalData.member_id)
        self.assertNsEqual(ns(data=result), dict(data=[]))

    def test_list_notFilteringByMember(self):
        partner_nonInvestorAndMember = 2 # TODO: Fragile
        id = self.Investment.create_from_form(
            self.personalData.partnerid,
            '2017-01-01', # order_date
            4000,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        name = self.Investment.read(id, ['name'])['name']

        result = self.list(member_id=None)
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
                investment_name=name,
                id = id,
                **self.personalData
            ))


unittest.TestCase.__str__ = unittest.TestCase.id

if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
