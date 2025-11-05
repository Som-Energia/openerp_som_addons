#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import pymongo
from generationkwh.memberrightsusage import MemberRightsUsage
import erppeek_wst
import dbconfig
import os
from subprocess import call
import sys
import genkwh_curve
from genkwh_curve import isodate
from yamlns import namespace as ns
import generationkwh.investmentmodel as gkwh
from somutils.testutils import destructiveTest

@destructiveTest
class CurveExporter_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        genkwh_curve.erp.value = self.erp
        self.Investment = self.erp.GenerationkwhInvestment
        self.clear()
        self.personaldata = ns(dbconfig.personaldata)
        self.member = self.personaldata.member_id
        self.shares = 26
        self.summerUp = range(1,25)+[0]
        self.summerDown = range(24,0,-1)+[0]

        self.erp.GenerationkwhMailmockup.activate()
        investment_id = self.Investment.create_from_form(
            self.personaldata.partnerid,
            '2049-08-14', # order_date
            self.shares*gkwh.shareValue,
            '10.10.23.123',
            'ES7712341234161234567890',
            )
        self.Investment.mark_as_invoiced(investment_id)
        self.Investment.mark_as_paid([investment_id],'2049-08-20')

    def tearDown(self):
        self.erp.GenerationkwhTesthelper.clear_mongo_collections([
            'rightspershare',
            'memberrightusage',
            ])
        self.erp.rollback()
        self.erp.close()

    def clear(self):
        #self.Investment.dropAll()
        self.erp.GenerationkwhRemainder.clean()
        self.erp.GenerationkwhTesthelper.clear_mongo_collections([
            'rightspershare',
            'memberrightusage',
            ])

    def assertCsvByColumnEqual(self, csv, columns):
        self.assertMultiLineEqual(
            csv,
            '\n'.join(
                '\t'.join( str(v) for v in row)
                for row in zip(*columns)
                )
            )

    def setupRights(self, shares, firstDate, data):
        self.erp.GenerationkwhTesthelper.setup_rights_per_share(
            shares, firstDate, data)

    def setupUsage(self, member, firstDate, data):
        self.erp.GenerationkwhTesthelper.memberrightsusage_update(
            member, firstDate, data)

    def test_dump_usage(self):

        usage = self.summerUp + self.summerDown

        self.setupUsage(self.member, '2050-08-15', usage)

        csv = genkwh_curve.dump(
            member=self.member,
            first=isodate('2050-08-15'),
            last =isodate('2050-08-17'),
            returnCsv=True,
            dumpUsage = True,
            dumpRights = False,
            dumpMemberShares = False,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['usage'] + usage+25*[0],
            ])

    def test_dump_shares(self):

        csv = genkwh_curve.dump(
            member=self.member,
            first=isodate('2050-08-19'),
            last =isodate('2050-08-21'),
            returnCsv=True,
            dumpUsage = False,
            dumpRights = False,
            dumpMemberShares = True,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['memberShares'] + 25*[0] + 25*2*[26],
            ])

    def test_dump_rights(self):

        rights = self.summerDown + self.summerUp
        self.setupRights(self.shares, '2050-08-20', rights)

        csv = genkwh_curve.dump(
            member=self.member,
            first=isodate('2050-08-19'),
            last =isodate('2050-08-22'),
            returnCsv=True,
            dumpUsage = False,
            dumpRights = True,
            dumpMemberShares = False,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['rights'] + 25*[0] + rights + 25*[0],
            ])



    def test_dump_rightsAndUsageByDefault(self):

        usage = self.summerUp + self.summerDown
        rights = self.summerDown + self.summerUp

        self.setupRights(self.shares, '2050-08-20', rights)
        self.setupUsage(self.member, '2050-08-20', usage)

        csv = genkwh_curve.dump(
            member=self.member,
            first=isodate('2050-08-20'),
            last =isodate('2050-08-22'),
            returnCsv=True,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['rights']+ rights+25*[0],
                ['usage'] + usage+25*[0],
            ])

    def test_dump_withMemberShares(self):

        usage = range(24,0,-1)+[0]
        rights = range(1,25)+[0]

        self.setupRights(self.shares, '2050-08-20', rights)
        self.setupUsage(self.member, '2050-08-20', usage)

        csv = genkwh_curve.dump(
            member=self.member,
            first=isodate('2050-08-20'),
            last =isodate('2050-08-20'),
            returnCsv=True,
            dumpMemberShares=True,
#            show=True,
            )
        self.assertCsvByColumnEqual(csv, [
                ['memberShares']+ 25*[self.shares],
                ['rights']+ rights,
                ['usage'] + usage,
            ])





if __name__ == '__main__':
    unittest.main()



