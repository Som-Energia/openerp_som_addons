# -*- coding: utf-8 -*-

import unittest
import datetime
from yamlns import namespace as ns
from generationkwh.isodates import isodate
import xmlrpclib
dbconfig = None
try:
    import dbconfig
    import erppeek_wst
except ImportError:
    pass

contract_stats="""
create temporary table contract_stats as
select
    p.id as partner,
    s.id as member,
    p.ref as code,
    s.id is not null as es_soci,  -- TODO: No mira si s'ha donat de baixa

    count(c.id) FILTER (WHERE c.id IS NOT NULL) as related,
    count(c.id) FILTER (WHERE p.id=c.titular AND p.id<>c.pagador) as nomes_titular,
    count(c.id) FILTER (WHERE p.id<>titular AND p.id=c.pagador) as nomes_pagador,
    count(c.id) FILTER (WHERE p.id=c.titular AND p.id=c.pagador) as titular_i_pagador,
    count(c.id) FILTER (WHERE p.id<>c.titular AND p.id<>c.pagador AND p.id=c.soci) as ha_apadrinat,
    count(c.id) FILTER (WHERE p.id<>c.soci) as ha_estat_apadrinat,

    p.name,

    array_agg(c.id) FILTER (WHERE p.id=c.titular AND p.id<>c.pagador) as contractes_nomes_titular,
    array_agg(c.id) FILTER (WHERE p.id<>titular AND p.id=c.pagador) as contractes_nomes_pagador,
    array_agg(c.id) FILTER (WHERE p.id=c.titular AND p.id=c.pagador) as contractes_titular_i_pagador,
    array_agg(c.id) FILTER (WHERE p.id<>c.titular AND p.id<>c.pagador AND p.id=c.soci) as contractes_ha_apadrinat,
    array_agg(c.id) FILTER (WHERE p.id<>c.soci) as contractes_ha_estat_apadrinat

from
    res_partner as p
left join
    somenergia_soci as s
        on p.id = s.partner_id
left join
    giscedata_polissa as c
        on p.id in (c.titular, c.soci, c.pagador)
        and c.active
        and c.state='activa'
group by p.id, p.name, p.ref, s.id
;
"""

caseLocator="""
select * from contract_stats as data
where %s
order by
    data.ha_apadrinat desc,
    data.related desc,
    data.partner asc
limit 1
;
"""

conditions = ns.loads("""
noContracts:   data.member is not null and data.related=0
oneAsPayer:  data.member is not null and data.related=1 and data.nomes_pagador=1
oneAsOwnerButNotPayer:  data.member is not null and data.related=1 and data.nomes_titular=1
oneAsPayerOtherAsOwner:  data.member is not null and data.related=2 and data.nomes_pagador=1 and data.nomes_titular=1
manyAsPayerManyAsOwner:  data.member is not null and data.related=5 and data.titular_i_pagador=3 and data.nomes_titular=2
manyAsPayer:  data.member is not null and data.related=2 and data.nomes_titular=2
""")

cases = ns()
if dbconfig:
    import dbutils
    import psycopg2
    with psycopg2.connect(**dbconfig.psycopg) as db:
        with db.cursor() as cr:
            cr.execute(contract_stats)
            for key, condition in conditions.items():
                cr.execute(caseLocator%condition)
                result = dbutils.nsList(cr)
                if not result:
                    raise Exception("Cannot find a case for {}".format(key))
                cases[key] = result[0]
                cases[key].condition = condition

#print cases.dump()


@unittest.skipIf(not dbconfig, "depends on ERP")
class Assignment_Test(unittest.TestCase):

    def setUp(self):
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Assignment = self.erp.GenerationkwhAssignment
        self.Assignment.dropAll()

        (
            self.member,
            self.member2,
            self.member3,
        ) = self.erp.SomenergiaSoci.search([],limit=3)
        (
            self.contract,
            self.contract2,
            self.contract3,
        ) = self.erp.GiscedataPolissa.search([], limit=3)
        self.today = str(datetime.date.today())

    def setupProvider(self,assignments=[]):
        for contract, member, priority in assignments:
            self.Assignment.create(dict(
                contract_id = contract,
                member_id = member,
                priority = priority,
                ))

    def assertAssignmentsEqual(self, expectation):
        result = self.Assignment.browse([], limit=None)
        self.assertEqual( [
                (
                    r.contract_id.id,
                    r.member_id.id,
                    r.priority,
                    r.end_date,
                )
                for r in result
            ],expectation)

    def tearDown(self):
        try:
            self.erp.rollback()
            self.erp.close()
        except xmlrpclib.Fault as e:
            if 'transaction block' not in e.faultCode:
                raise

    def test_no_assignments(self):
        self.setupProvider()
        self.assertAssignmentsEqual([])

    def test_default_values(self):
        self.Assignment.create(dict(
            member_id = self.member,
            contract_id = self.contract,
            priority = 0,
            ))
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0, False),
            ])

    def test_create_priorityRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                member_id = self.member,
                contract_id = self.contract,
                ))
        self.assertRegexpMatches(
            #'null value in column "priority" violates not-null constraint',
            str(ctx.exception),
            'Integrity.*Error.*priority.*not.*null')

    def test_create_contractRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                member_id = self.member,
                priority = 0,
                ))
        self.assertRegexpMatches(
            #'null value in column "priority" violates not-null constraint',
            str(ctx.exception),
            'Integrity.*Error.*contract_id.*not.*null')

    def test_create_memberRequired(self):

        with self.assertRaises(Exception) as ctx:
            self.Assignment.create(dict(
                contract_id = self.contract,
                priority = 0,
                ))
        self.assertRegexpMatches(
            #'null value in column "priority" violates not-null constraint',
            str(ctx.exception),
            'Integrity.*Error.*member_id.*not.*null')

    def test_one_assignment(self):
        self.setupProvider([
            (self.contract,self.member,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract,self.member,1,False),
            ])

    def test_no_duplication(self):
        self.setupProvider([
            (self.contract, self.member, 1),
            (self.contract, self.member, 2),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 1, self.today),
            (self.contract, self.member, 2, False),
            ])

    def test_change_priority(self):
        self.setupProvider([
            (self.contract,self.member,1),
            (self.contract,self.member,2),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 1, self.today),
            (self.contract, self.member, 2, False),
            ])

    def test_three_member_three_polissas(self):
        members=self.member, self.member2, self.member3
        contracts=self.contract,self.contract2,self.contract3
        self.setupProvider([
            (self.contract, self.member, 1),
            (self.contract2,self.member2,1),
            (self.contract3,self.member3,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 1,False),
            (self.contract2,self.member2,1,False),
            (self.contract3,self.member3,1,False),
            ])

    def test_three_member_one_polissa(self):
        members=self.member, self.member2, self.member3
        self.setupProvider([
            (self.contract,self.member, 1),
            (self.contract,self.member2,1),
            (self.contract,self.member3,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract,self.member, 1,False),
            (self.contract,self.member2,1,False),
            (self.contract,self.member3,1,False),
            ])

    def test_one_member_three_polissas(self):
        contracts=self.contract,self.contract2,self.contract3
        self.setupProvider([
            (self.contract,  self.member,1),
            (self.contract2, self.member,1),
            (self.contract3, self.member,1),
            ])
        self.assertAssignmentsEqual([
            (self.contract , self.member,1,False),
            (self.contract2, self.member,1,False),
            (self.contract3, self.member,1,False),
            ])

    def test_expire_one_member_one_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsEqual([
            (self.contract, self.member,1,self.today),
            ])

    def test_expire_one_member_two_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            (self.contract2, self.member,1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsEqual([
            (self.contract, self.member,1,self.today),
            (self.contract2, self.member,1,False),
            ])

    def test_expire_previously_expired_polissa(self):
        self.setupProvider([
            (self.contract, self.member,1),
            (self.contract, self.member,1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsEqual([
            (self.contract, self.member,1,self.today),
            (self.contract, self.member,1,self.today),
            ])

@unittest.skipIf(not dbconfig, "depends on ERP")
class AssignmentProvider_Test(unittest.TestCase):

    def orderContractsByConany(self,contract_ids):
        unorderedContracts = self.erp.GiscedataPolissa.browse(contract_ids)
        unorderedCups_ids = [pol.cups.id for pol in unorderedContracts if pol.cups.active]
        orderedCups_ids = self.erp.GiscedataCupsPs.search([('id','in', unorderedCups_ids)],order='conany_kwh DESC')
        orderedCups = self.erp.GiscedataCupsPs.browse(orderedCups_ids)
        return tuple([cups.polissa_polissa.id for cups in orderedCups])

    def setUp(self):
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.Assignment = self.erp.GenerationkwhAssignment
        self.AssignmentTestHelper = self.erp.GenerationkwhAssignmentTesthelper
        self.Assignment.dropAll()

        self.member, self.member2 = [
            m.id for m in self.erp.SomenergiaSoci.browse([], limit=2)]

        contract, contract2 = [ c for c in self.erp.GiscedataPolissa.browse(
                [('data_ultima_lectura','!=',False)],
                order='data_ultima_lectura',
                limit=2,
                )
            ]
        self.contract = contract.id
        self.contract2 = contract2.id
        self.contractLastInvoicedDate = contract.data_ultima_lectura
        self.contract2LastInvoicedDate = contract2.data_ultima_lectura
        self.today = str(datetime.date.today())

        newContract, = self.erp.GiscedataPolissa.browse(
                [('data_ultima_lectura','=',False),
                 ('state','=','activa')], limit=1)
        self.newContract = newContract.id
        self.newContractActivationDate = newContract.data_alta

    def setupAssignments(self, assignments):
        for contract, member, priority in assignments:
            self.Assignment.create(dict(
                contract_id=contract,
                member_id=member,
                priority=priority,
                ))

    def assertAssignmentsSeekEqual(self, contract_id, expectation):
        result = self.Assignment.contractSources(contract_id)
        self.assertEqual([
            (member_id, last_usable_date)
            for member_id, last_usable_date in expectation
            ], [
            (member_id, last_usable_date)
            for member_id, last_usable_date in result
            ])

        result = self.AssignmentTestHelper.contractSources(contract_id)
        self.assertEqual([
            dict(
                member_id=member_id,
                last_usable_date=last_usable_date,
            )
            for member_id, last_usable_date in expectation
            ], result)

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    def test_contractSources_noAssignment(self):
        self.setupAssignments([])
        self.assertAssignmentsSeekEqual(self.contract, [])

    def test_contractSources_oneAssignment_noCompetitors(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            ])

    def test_contractSources_expiredAssignment_notRetrieved(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.Assignment.expire(self.contract, self.member)
        self.assertAssignmentsSeekEqual(self.contract, [
            ])

    def test_contractSources_assigmentsForOtherContracts_ignored(self):
        self.setupAssignments([
            (self.contract2, self.member, 1),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
        ])

    def test_contractSources_manyAssignments_noCompetitors(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract, self.member2, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            (self.member2, self.today),
            ])

    def test_contractSources_competitorWithoutInvoices_takesActivationDate(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.newContract, self.member, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.newContractActivationDate),
            ])

    def test_contractSources_competitorWithInvoices_takesLastInvoicedDate(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 0),
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.contract2LastInvoicedDate),
            ])

    def test_contractSources_competitor_expired_ignored(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 0),
            ])
        self.Assignment.expire(self.contract2, self.member)
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            ])

    def test_contractSources_competitorWithEqualOrLowerPriority_ignored(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member, 1), # equal
            (self.newContract, self.member, 2), # lower (higher number)
            ])
        self.assertAssignmentsSeekEqual(self.contract, [
            (self.member, self.today),
            ])

    def test_contractSources_manyCompetitors_earlierLastInvoicedPrevails(self):
        self.setupAssignments([
            (self.newContract,self.member,1),
            (self.contract,self.member,0),
            (self.contract2,self.member,0),
            ])
        self.assertAssignmentsSeekEqual(self.newContract, [
            (self.member, min(
                self.contractLastInvoicedDate,
                self.contract2LastInvoicedDate,
                )),
            ])

    def assertAssignmentsEqual(self,expectation):
        self.assertEqual([
            (record.contract_id.id, record.member_id.id, record.priority)
            for record in self.Assignment.browse([], order='id')
            ], expectation)

    def test_createOnePrioritaryAndManySecondaries_oneAssignment(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_noAssignment(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            ])
        self.assertAssignmentsEqual([
            ])

    def test_createOnePrioritaryAndManySecondaries_clearPrevious(self):
        self.setupAssignments([
            (self.contract2, self.member, 1),
            ])
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_preserveOtherMembers(self):
        self.setupAssignments([
            (self.contract2, self.member2, 1),
            ])
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract,self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract2, self.member2, 1),
            (self.contract, self.member, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_manyMembers_singleContract(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract,self.member),
            (self.contract2,self.member2),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            (self.contract2, self.member2, 0),
            ])

    def test_createOnePrioritaryAndManySecondaries_sameMember_manyContracts(self):
        self.Assignment.createOnePrioritaryAndManySecondaries([
            (self.contract, self.member),
            (self.contract2, self.member),
            ])
        self.assertAssignmentsEqual([
            (self.contract, self.member, 0),
            (self.contract2, self.member, 1),
            ])


    def assertContractForMember(self, member_id,expectation):
        if not isinstance(member_id,list):
            member_ids=[member_id]
        else:
            member_ids=member_id
        result=self.Assignment.sortedDefaultContractsForMember(
            member_ids
        )
        self.assertEqual([tuple(r) for r in result], expectation)


    def test_sortedDefaultContractsForMember_noMembersSpecified(self):
        self.assertContractForMember([], [
            ])

    def test_sortedDefaultContractsForMember_withoutContracts(self):
        member = cases.noContracts.member
        self.assertContractForMember(member, [
            ])

    def test_sortedDefaultContractsForMember_oneAsPayer(self):
        member = cases.oneAsPayer.member
        contract = cases.oneAsPayer.contractes_nomes_pagador[0]
        self.assertContractForMember(member, [
            (contract, member),
            ])

    def test_sortedDefaultContractsForMember_oneAsOwnerButNotPayer(self):
        member = cases.oneAsOwnerButNotPayer.member
        contract = cases.oneAsOwnerButNotPayer.contractes_nomes_titular[0]
        self.assertContractForMember(member, [
            (contract, member),
            ])

    def test_sortedDefaultContractsForMember_onePayerAndOneOwner_payerFirst(self):
        member = cases.oneAsPayerOtherAsOwner.member
        contractAsPayer = cases.oneAsPayerOtherAsOwner.contractes_nomes_pagador[0]
        contractAsOwner = cases.oneAsPayerOtherAsOwner.contractes_nomes_titular[0]
        self.assertContractForMember(member, [
            (contractAsPayer, member),
            (contractAsOwner, member),
            ])

    def test_sortedDefaultContractsForMember_manyAsPayer_biggerFirst(self):
        case = cases.manyAsPayer
        member = case.member
        contracts = self.orderContractsByConany(case.contractes_nomes_titular)
        self.assertContractForMember([
            member,
            ], [
                (contracts[0], member),
                (contracts[1], member),
            ])

    def test_sortedDefaultContractsForMember_manyAsPayerAndManyAsOwner(self):
        # TODO: Check the order is right
        case = cases.manyAsPayerManyAsOwner
        member = case.member
        payerContracts = self.orderContractsByConany(case.contractes_titular_i_pagador)
        ownerContracts = self.orderContractsByConany(case.contractes_nomes_titular)
        self.assertContractForMember([
            member,
            ], [
            (payerContracts[0], member),
            (payerContracts[1], member),
            (payerContracts[2], member),
            (ownerContracts[0], member),
            (ownerContracts[1], member),
            ])

    def test_sortedDefaultContractsForMember_severalMembers_doNotBlend(self):
        case1 = cases.manyAsPayer
        member1 = case1.member
        contracts1 = self.orderContractsByConany(case1.contractes_nomes_titular)

        case2 = cases.manyAsPayerManyAsOwner
        member2 = case2.member
        payerContracts = self.orderContractsByConany(case2.contractes_titular_i_pagador)
        ownerContracts = self.orderContractsByConany(case2.contractes_nomes_titular)
        self.assertContractForMember([
            member1,
            member2,
            ], [
            (contracts1[0], member1),
            (contracts1[1], member1),
            (payerContracts[0], member2),
            (payerContracts[1], member2),
            (payerContracts[2], member2),
            (ownerContracts[0], member2),
            (ownerContracts[1], member2),
            ])

    def test_anyForContract_noActiveContracts(self):
        result = self.Assignment.anyForContract(99999999)
        self.assertEqual(result,False)

    def test_anyForContract_ActiveOtherContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        result = self.Assignment.anyForContract(99999999)
        self.assertEqual(result,False)

    def test_anyForContract_ActiveOneContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,True)

    def test_anyForContract_ExpiredContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.Assignment.expire(self.contract,self.member)
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,False)

    def test_anyForContract_ExpiredAndActiveContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            ])
        self.Assignment.create({
            'contract_id':self.contract,
            'member_id':self.member,
            'priority': 1
            })
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,True)

    def test_anyForContract_OtherExpiredActiveContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member2, 1),
            ])
        self.Assignment.expire(self.contract,self.member)
        result = self.Assignment.anyForContract(self.contract2)
        self.assertEqual(result,True)

    def test_anyForContract_OtherActiveExpiredContract(self):
        self.setupAssignments([
            (self.contract, self.member, 1),
            (self.contract2, self.member2, 1),
            ])
        self.Assignment.expire(self.contract,self.member)
        result = self.Assignment.anyForContract(self.contract)
        self.assertEqual(result,False)



unittest.TestCase.__str__ = unittest.TestCase.id

if __name__ == '__main__':
    unittest.main()

# vim: et ts=4 sw=4
