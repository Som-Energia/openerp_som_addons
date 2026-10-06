# -*- coding: utf-8 -*-

import unittest

class Dealer_test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        import erppeek_wst
        import dbconfig
        self.c = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.c.begin()
        self.helper = self.c.GenerationkwhTesthelper
        self.DealerApi = self.c.GenerationkwhDealer
        self.clearData()
        self.contract, self.contract2 = self.c.GiscedataPolissa.search([], limit=2)
        self.member = 1 # has 25 shares at the first investment wave
        self.partner = 2
        self.member2 = 469
        self.partner2 = 550

    def tearDown(self):
        self.c.rollback()
        self.c.close()

    def clearData(self):
        self.c.GenerationkwhAssignment.dropAll()
        self.c.GenerationkwhInvestment.dropAll()
    
    def assertContractActive(self, expectation, contract, first, last):
        result = self.helper.dealer_is_active(contract, first, last)
        self.assertEqual(result,expectation)
        result = self.DealerApi.is_active(contract, first, last)
        self.assertEqual(result,expectation)

    def _test__is_active__withBadContract(self):
        self.assertContractActive(False,
            999999999,'2016-08-15','2016-08-15')
    
    def test__is_active__withoutAssignments(self):
        self.assertContractActive(False,
            self.contract,'2016-08-15','2016-08-15')

    def test__is_active__withAssignments_andActiveInvestments(self):
        self.c.GenerationkwhInvestment.create_from_accounting(self.member,None,None,1,None)
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.assertContractActive(True,
            self.contract,'2016-08-15','2016-08-15')

    def test__is_active__withAssignments_butNoInvestments(self):
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.assertContractActive(False,
            self.contract,'2016-08-15','2016-08-15')

    def test__is_active__withAssignments_andIneffectiveInvestments(self):
        self.c.GenerationkwhInvestment.create_from_accounting(self.member,None,None,None,None)
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.assertContractActive(False,
            self.contract,'2016-08-15','2016-08-15')

    def test__is_active__withAssignments_andNotYetActiveInvestments(self):
        self.c.GenerationkwhInvestment.create_from_accounting(self.member,None,None,1,3)
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.assertContractActive(False,
            self.contract,'2014-08-15','2014-08-15')

    def test__is_active__withAssignments_andExpiredInvestments(self):
        self.c.GenerationkwhInvestment.create_from_accounting(self.member,None,None,1,1)
        self.c.GenerationkwhAssignment.create(
            dict(contract_id=self.contract, member_id=self.member, priority=1))
        self.assertContractActive(False,
            self.contract,'2046-08-15','2046-08-15')

if __name__ == '__main__':
    unittest.main()

# vim: et ts=4 sw=4
