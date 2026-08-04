# -*- coding: utf-8 -*-

import datetime
import unittest
from somutils.testutils import destructiveTest

dbconfig = None
try:
    import dbconfig
    import erppeek_wst
except ImportError:
    pass

binsPerDay = 25

@unittest.skipIf(not dbconfig, "depends on ERP")
class IdMappers_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.c = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.c.begin()

    def tearDown(self):
        self.c.rollback()
        self.c.close()

    def test_map_member_by_partners_all_in(self):
        map={
            5:4,
            61:54,
            120:107,
            400:351,
            629:537,
            }
        result=self.c.GenerationkwhDealer.get_members_by_partners(
            map.keys()
            )
        self.assertEqual(map,dict(result))

    def test_map_member_by_partners_not_all_in(self):
        result=self.c.GenerationkwhDealer.get_contracts_by_ref('1')
        self.assertEqual({'1':1},dict(result))

    def test_map_member_by_partners_not_all_in(self):
        map={629:537, 5:4, 120:107, 61:54, 400:351}

        result=self.c.GenerationkwhDealer.get_members_by_partners(
            list(map.keys())+[999999]
            )
        self.assertEqual(map,dict(result))


    def test_map_partners_by_members_all_in(self):
        map={537:629, 4:5, 107:120, 54:61, 351:400,}
        result=self.c.GenerationkwhDealer.get_partners_by_members(
            list(map.keys())
            )
        self.assertEqual(map,dict(result))

    def test_map_partners_by_members_not_all_in(self):
        map={537:629, 4:5, 107:120, 54:61, 351:400,}
        result=self.c.GenerationkwhDealer.get_partners_by_members(
            list(map.keys())+[999999]
            )
        self.assertEqual(map,dict(result))

    def test_getMembersByCode(self):
        map={1620:1911}
        result=self.c.GenerationkwhDealer.get_members_by_codes(
            list(map.keys())
            )
        self.assertEqual({"S001620":1585},dict(result))


@unittest.skipIf(not dbconfig, "depends on ERP")
@destructiveTest
class UsageTracker_Test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        self.c = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.c.begin()
        self.clearData()
        self.contract = 4
        self.member = 1 # has 25 shares at the first investment wave
        self.partner = 2
        self.member2 = 469
        self.partner2 = 550
        self.nonMemberPartner = 1 # SomEnergia
        self.fareId = 1 # 2.0A
        self.periodId = 1 # 2.0A P1

    def createInvestments(self, start=None, stop=None, waitingDays=None, expirationYears=None):
        Investment = self.c.GenerationkwhInvestment
        member = [self.member, self.member2]
        Investment.create_from_accounting(member, start, stop, waitingDays, expirationYears)

    def tearDown(self):
        self.clearMongo()
        self.c.rollback()
        self.c.close()

    def clearMongo(self):
        self.c.GenerationkwhTesthelper.clear_mongo_collections([
            'rightspershare',
            'memberrightusage',
            ])

    def clearData(self):
        self.clearMongo()
        self.c.GenerationkwhInvestment.dropAll()
        self.c.GenerationkwhAssignment.dropAll()
        self.c.GenerationkwhRemainderTesthelper.clean()

    def test_available_kwh_withNoActiveShares(self):
        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                4, '2016-08-01', '2016-09-01', '2.0A', 'P1'),
            0)
    def test_available_kwh_rightsAndInvestments(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            3*2*24)

    def test_available_kwh_noRights(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            20, '2015-08-01', [2]*2*binsPerDay)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            69, '2015-08-01', [0]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            0*2*24)


    def test_available_kwh_rightsForOne(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            1, '2015-08-01', [2]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_available_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1'),
            50*2*24)

        # TODO: assert remainder has been added

    def test_use_kwh_exhaustingAvailable(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 3*2*24+100),
            3*2*24)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            +24*[3]+1*[0]
            +24*[3]+1*[0]
            +25*[0]
            )


    def test_use_kwh__notExhaustingAvailable(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10),
            10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            +3*[3]+[1]+21*[0]
            +25*[0]
            +25*[0]
            )

    def test_use_kwh__consumingOnConsumedDays(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10),
            10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 3*2*24+100),
            3*2*24-10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            +24*[3]+[0]
            +24*[3]+[0]
            +25*[0]
            )

    def test_refund_kwh(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_use_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10),
            10)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usagetracker_refund_kwh(
                self.member, '2015-08-01', '2015-09-01', '2.0A', 'P1', 2),
            2)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [3,3,2]+22*[0]
            +25*[0]
            +25*[0]
            )


    def test_dealer__use_kwh(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [0,3,0,0,0])
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            5, '2015-08-01', [0,0,7,0,0])

        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=0))
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member2, priority=0))

#        self.c.GenerationkwhTesthelper.trace_rigths_compilation(
#            self.member2, '2015-08-01', '2015-09-01', '2.0A', 'P1')

        self.assertEqual(
            self.c.GenerationkwhTesthelper.dealer_use_kwh(
                self.contract, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10), [
                dict(member_id=self.member, kwh=3),
                dict(member_id=self.member2, kwh=7),
            ])

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [0,3,0]+22*[0]
            +25*[0]
            +25*[0]
            )

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member2, '2015-08-01', '2015-08-03'),
            [0,0,7]+22*[0]
            +25*[0]
            +25*[0]
            )

    def test_dealer__refund_kwh(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=0))

        self.assertEqual(
            self.c.GenerationkwhTesthelper.dealer_use_kwh(
                self.contract, '2015-08-01', '2015-09-01', '2.0A', 'P1', 10), [
                dict(member_id=self.member, kwh=10),
            ])

        self.assertEqual(
            self.c.GenerationkwhTesthelper.dealer_refund_kwh(
                self.contract, '2015-08-01', '2015-09-01', '2.0A', 'P1', 2, self.member),
            2)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [3,3,2]+22*[0]
            +25*[0]
            +25*[0]
            )


    def test_dealerApi__use_kwh__turnsPartnersIds(self):
        # Investments
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        # Production
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [0,3,0,0,0])
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            5, '2015-08-01', [0,0,7,0,0])
        # Assignments
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=0))
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member2, priority=0))

#        self.c.GenerationkwhTesthelper.trace_rigths_compilation(
#            self.partner2, '2015-08-01', '2015-09-01', '2.0A', 'P1')

        self.assertEqual(
            self.c.GenerationkwhDealer.use_kwh(
                self.contract, '2015-08-01', '2015-09-01', self.fareId, self.periodId, 10), [
                dict(member_id=self.partner, kwh=3),
                dict(member_id=self.partner2, kwh=7),
            ])

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [0,3,0]+22*[0]
            +25*[0]
            +25*[0]
            )

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member2, '2015-08-01', '2015-08-03'),
            [0,0,7]+22*[0]
            +25*[0]
            +25*[0]
            )

    def test_dealerApi__refund_kwh__turnsPartnerIds(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=0))

        self.assertEqual(
            self.c.GenerationkwhDealer.use_kwh(
                self.contract, '2015-08-01', '2015-09-01', self.fareId, self.periodId, 10), [
                dict(member_id=self.partner, kwh=10), # Here
            ])

        self.assertEqual(
            self.c.GenerationkwhDealer.refund_kwh(
                self.contract, '2015-08-01', '2015-09-01', self.fareId, self.periodId, 2, self.partner), # and Here
            2)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [3,3,2]+22*[0]
            +25*[0]
            +25*[0]
            )

    def test_dealerApi__refund_kwh__withNonMemberPartner_doNotRefund(self):
        self.createInvestments(stop="2015-06-30", waitingDays=0)
        self.c.GenerationkwhTesthelper.setup_rights_per_share(
            25, '2015-08-01', [3]*2*binsPerDay)

        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=0))

        self.assertEqual(
            self.c.GenerationkwhDealer.use_kwh(
                self.contract, '2015-08-01', '2015-09-01', self.fareId, self.periodId, 10), [
                dict(member_id=self.partner, kwh=10), # Here
            ])

        self.assertEqual(
            self.c.GenerationkwhDealer.refund_kwh(
                self.contract, '2015-08-01', '2015-09-01', self.fareId, self.periodId, 2, self.nonMemberPartner),
            0)

        self.assertEqual(
            self.c.GenerationkwhTesthelper.usage(self.member, '2015-08-01', '2015-08-03'),
            [3,3,3,1]+21*[0]
            +25*[0]
            +25*[0]
            )
if __name__ == '__main__':
	unittest.TestCase.__str__ = unittest.TestCase.id
	unittest.main()


