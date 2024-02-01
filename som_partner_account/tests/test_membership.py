# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
import unittest
from osv import fields
from yamlns import namespace as ns


class TestAccountAccountSom(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.adopter = self.get_ref("base", "main_partner")
        self.barbara = self.get_ref("base", "res_partner_c2c")
        self.cecilia = self.get_ref("base", "res_partner_agrolait")
        self.contract1_id = self.get_ref("giscedata_polissa", "polissa_0001")
        self.contract2_id = self.get_ref("giscedata_polissa", "polissa_0002")
        self.member_category = self.get_ref("som_partner_account", "res_partner_category_soci")
        self.partner_id = self.get_ref("base", "res_partner_c2c")

    def tearDown(self):
        self.txn.stop()

    def get_ref(self, module, ref):
        IrModel = self.openerp.pool.get("ir.model.data")
        return IrModel._get_obj(self.cursor, self.uid, module, ref).id

    def getCategories(self, partner_id):
        Partner = self.openerp.pool.get("res.partner")
        partner = Partner.read(
            self.cursor,
            self.uid,
            partner_id,
            [
                "category_id",
            ],
        )
        return partner["category_id"]

    def test__become_member__addsCategory(self):
        Partner = self.openerp.pool.get("res.partner")

        oldCategories = self.getCategories(self.partner_id)

        Partner.become_member(self.cursor, self.uid, self.partner_id)

        self.assertEqual(
            oldCategories + [self.member_category],
            self.getCategories(self.partner_id),
        )

    def test__become_member__doNotAddCategoryTwice(self):
        Partner = self.openerp.pool.get("res.partner")

        oldCategories = self.getCategories(self.partner_id)
        Partner.write(
            self.cursor, self.uid, self.partner_id, {"category_id": [(4, self.member_category)]}
        )

        Partner.become_member(self.cursor, self.uid, self.partner_id)

        self.assertEqual(
            oldCategories + [self.member_category], self.getCategories(self.partner_id)
        )

    def test__become_member__withNoPreviousRef(self):
        Partner = self.openerp.pool.get("res.partner")

        Partner.write(
            self.cursor,
            self.uid,
            self.partner_id,
            dict(
                ref="",  # No ref
            ),
        )

        Partner.become_member(self.cursor, self.uid, self.partner_id)

        partner = Partner.read(self.cursor, self.uid, self.partner_id, ["ref"])

        self.assertRegexpMatches(
            partner["ref"],
            "S[0-9]{6}",
        )

    def test__become_member__withPreviousMemberRef_keepsIt(self):
        Partner = self.openerp.pool.get("res.partner")

        Partner.write(
            self.cursor,
            self.uid,
            self.partner_id,
            dict(
                ref="S666666",  # Valid member ref
            ),
        )

        Partner.become_member(self.cursor, self.uid, self.partner_id)

        partner = Partner.read(self.cursor, self.uid, self.partner_id, ["ref"])

        self.assertEqual(partner["ref"], "S666666")

    def test__become_member__withNonMemberRef_changesIt(self):
        Partner = self.openerp.pool.get("res.partner")

        Partner.write(
            self.cursor,
            self.uid,
            self.partner_id,
            dict(
                ref="T666666",  # Valid non member ref
            ),
        )

        Partner.become_member(self.cursor, self.uid, self.partner_id)

        partner = Partner.read(self.cursor, self.uid, self.partner_id, ["ref"])

        self.assertRegexpMatches(
            partner["ref"],
            "S[0-9]{6}",
        )

    from plantmeter.testutils import assertNsEqual

    def test__become_member__createsMember(self):
        Partner = self.openerp.pool.get("res.partner")
        Member = self.openerp.pool.get("somenergia.soci")

        member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)

        self.assertTrue(member_id)

        member = Member.read(
            self.cursor,
            self.uid,
            member_id,
            [
                "partner_id",
                "data_baixa_soci",
                "baixa",
            ],
        )

        member = ns(member)
        member.partner_id = member.partner_id[0]

        self.assertNsEqual(
            member,
            ns(
                data_baixa_soci=False,
                baixa=False,
                id=member_id,
                partner_id=self.partner_id,
            ),
        )

    def test__become_member__whenMemberExist_keeps(self):
        Partner = self.openerp.pool.get("res.partner")
        Member = self.openerp.pool.get("somenergia.soci")

        old_member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)

        member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)

        self.assertEqual(old_member_id, member_id)

        member = Member.read(self.cursor, self.uid, member_id, ["comment"])
        self.assertEqual(member["comment"], "")

    def test__become_member__whenMemberDroppedOut(self):
        Partner = self.openerp.pool.get("res.partner")
        Member = self.openerp.pool.get("somenergia.soci")

        old_member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)
        Member.write(
            self.cursor,
            self.uid,
            old_member_id,
            dict(
                data_baixa_soci="2010-01-01",
                baixa=True,
                comment="",
            ),
        )

        member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)

        self.assertEqual(old_member_id, member_id)
        member = Member.read(
            self.cursor,
            self.uid,
            member_id,
            [
                "data_baixa_soci",
                "baixa",
                "comment",
            ],
        )
        self.assertNsEqual(
            ns(member),
            u"""
            data_baixa_soci: false
            baixa: false
            id: {id}
            comment: "{today:%Y-%m-%d} Donat d'alta quan estava de baixa des de 2010-01-01"
            """.format(
                id=member_id,
                today=date.today(),
            ),
        )

    def test__become_member__whenMemberDroppedOut_withPreviousComment_appends(self):
        Partner = self.openerp.pool.get("res.partner")
        Member = self.openerp.pool.get("somenergia.soci")

        old_member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)
        Member.write(
            self.cursor,
            self.uid,
            old_member_id,
            dict(
                data_baixa_soci="2010-01-01",
                baixa=True,
                comment="Previous comment",
            ),
        )

        member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)

        member = Member.read(
            self.cursor,
            self.uid,
            member_id,
            [
                "comment",
            ],
        )
        self.assertEqual(
            member["comment"],
            "Previous comment\n"
            "{today:%Y-%m-%d} Donat d'alta quan estava de baixa des de 2010-01-01".format(
                today=date.today()
            ),
        )

    def test__become_member__whenCommentExists_doNotInsertNewLine(self):
        Partner = self.openerp.pool.get("res.partner")
        Member = self.openerp.pool.get("somenergia.soci")

        old_member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)
        Partner.write(self.cursor, self.uid, self.partner_id, dict(comment="Previous comment"))

        member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)

        self.assertEqual(old_member_id, member_id)

        member = Member.read(self.cursor, self.uid, member_id, ["comment"])
        self.assertEqual(member["comment"], "Previous comment")

    def test__become_member__whenInactive(self):
        Partner = self.openerp.pool.get("res.partner")
        Member = self.openerp.pool.get("somenergia.soci")

        old_member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)
        Member.write(
            self.cursor,
            self.uid,
            old_member_id,
            dict(
                active=False,
                data_baixa_soci="2010-01-01",
                baixa=True,
                comment="Previous comment",
            ),
        )

        member_id = Partner.become_member(self.cursor, self.uid, self.partner_id)

        self.assertEqual(member_id, old_member_id)

        member = Member.read(
            self.cursor,
            self.uid,
            member_id,
            [
                "active",
                "data_baixa_soci",
                "baixa",
                "comment",
            ],
        )

        self.assertNsEqual(
            ns(member),
            """\
            id: {id}
            active: True
            data_baixa_soci: False
            baixa: false
            comment: "Previous comment\\n{today:%Y-%m-%d} Donat d'alta quan estava de baixa des de 2010-01-01"
        """.format(
                id=member_id,
                today=date.today(),
            ),
        )

    def assertContractPeople(self, contract_id, member, owner, payer):
        Contract = self.openerp.pool.get("giscedata.polissa")

        contract = Contract.read(
            self.cursor,
            self.uid,
            contract_id,
            [
                "titular",
                "soci",
                "pagador",
            ],
        )
        contract["titular"] = contract["titular"] and contract["titular"][0]
        contract["pagador"] = contract["pagador"] and contract["pagador"][0]
        contract["soci"] = contract["soci"] and contract["soci"][0]

        self.assertNsEqual(
            ns(contract),
            u"""\
            id: {contract_id}
            titular: {owner}
            pagador: {payer}
            soci: {member}
        """.format(
                **locals()
            ),
        )

    def test__adopt_contracts_as_member__newMemberIsContractOwner(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.adopter,
                pagador=self.barbara,
                soci=self.cecilia,
            ),
        )

        contract_ids = Partner.adopt_contracts_as_member(self.cursor, self.uid, self.adopter)

        self.assertEqual(contract_ids, [self.contract1_id])
        self.assertContractPeople(
            self.contract1_id,
            owner=self.adopter,
            payer=self.barbara,
            member=self.adopter,
        )

    def test__adopt_contracts_as_member__withNoContractsRelated(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        contract_ids = Partner.adopt_contracts_as_member(self.cursor, self.uid, self.adopter)

        self.assertEqual(contract_ids, [])

    def test__adopt_contracts_as_member__newMemberIsContractPayer(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.barbara,
                pagador=self.adopter,
                soci=self.cecilia,
            ),
        )

        contract_ids = Partner.adopt_contracts_as_member(self.cursor, self.uid, self.adopter)

        self.assertEqual(contract_ids, [self.contract1_id])
        self.assertContractPeople(
            self.contract1_id,
            owner=self.barbara,
            payer=self.adopter,
            member=self.adopter,
        )

    def test__adopt_contracts_as_member__withManyContractsRelated(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.barbara,
                pagador=self.adopter,
                soci=self.cecilia,
            ),
        )

        Contract.write(
            self.cursor,
            self.uid,
            self.contract2_id,
            dict(
                titular=self.adopter,
                pagador=self.barbara,
                soci=self.cecilia,
            ),
        )

        contract_ids = Partner.adopt_contracts_as_member(self.cursor, self.uid, self.adopter)

        self.assertEqual(contract_ids, [self.contract1_id, self.contract2_id])
        self.assertContractPeople(
            self.contract1_id,
            owner=self.barbara,
            payer=self.adopter,
            member=self.adopter,
        )
        self.assertContractPeople(
            self.contract2_id,
            owner=self.adopter,
            payer=self.barbara,
            member=self.adopter,
        )

    def test__adopt_contracts_as_member__payerIsMember_keepsIt(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.adopter,
                pagador=self.barbara,
                soci=self.barbara,
            ),
        )

        contract_ids = Partner.adopt_contracts_as_member(self.cursor, self.uid, self.adopter)

        self.assertEqual(contract_ids, [])
        self.assertContractPeople(
            self.contract1_id,
            owner=self.adopter,
            payer=self.barbara,
            member=self.barbara,
        )

    def test__adopt_contracts_as_member__ownerIsMember_keepsIt(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.barbara,
                pagador=self.adopter,
                soci=self.barbara,
            ),
        )

        contract_ids = Partner.adopt_contracts_as_member(self.cursor, self.uid, self.adopter)

        self.assertEqual(contract_ids, [])
        self.assertContractPeople(
            self.contract1_id,
            owner=self.barbara,
            payer=self.adopter,
            member=self.barbara,
        )

    def test__adopt_contracts_as_member__withNoPreviousMember_doesNotCrash(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.barbara,
                pagador=self.adopter,
                soci=False,
            ),
        )

        contract_ids = Partner.adopt_contracts_as_member(self.cursor, self.uid, self.adopter)

        self.assertEqual(contract_ids, [self.contract1_id])
        self.assertContractPeople(
            self.contract1_id,
            owner=self.barbara,
            payer=self.adopter,
            member=self.adopter,
        )

    def test__button_assign_soci_seq__createsMember(self):
        Partner = self.openerp.pool.get("res.partner")
        Member = self.openerp.pool.get("somenergia.soci")

        Partner.button_assign_soci_seq(self.cursor, self.uid, self.partner_id)

        member_id = Member.search(
            self.cursor,
            self.uid,
            [
                ("partner_id", "=", self.partner_id),
            ],
        )[0]

        self.assertTrue(member_id)

        member = Member.read(
            self.cursor,
            self.uid,
            member_id,
            [
                "partner_id",
                "data_baixa_soci",
                "baixa",
            ],
        )

        member = ns(member)
        member.partner_id = member.partner_id[0]

        self.assertNsEqual(
            member,
            ns(
                data_baixa_soci=False,
                baixa=False,
                id=member_id,
                partner_id=self.partner_id,
            ),
        )

    def test__button_assign_soci_seq__adoptsContract(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.adopter,
                pagador=self.cecilia,
                soci=self.barbara,
            ),
        )

        Partner.button_assign_soci_seq(self.cursor, self.uid, self.adopter)

        self.assertContractPeople(
            self.contract1_id,
            owner=self.adopter,
            payer=self.cecilia,
            member=self.adopter,
        )

    def test__button_assign_soci_seq__withManyMembers(self):
        Partner = self.openerp.pool.get("res.partner")
        Contract = self.openerp.pool.get("giscedata.polissa")

        Contract.write(
            self.cursor,
            self.uid,
            self.contract1_id,
            dict(
                titular=self.adopter,
                pagador=self.cecilia,
                soci=self.barbara,
            ),
        )

        Contract.write(
            self.cursor,
            self.uid,
            self.contract2_id,
            dict(
                titular=self.cecilia,
                pagador=self.cecilia,
                soci=self.barbara,
            ),
        )

        Partner.button_assign_soci_seq(
            self.cursor,
            self.uid,
            [
                self.adopter,
                self.cecilia,
            ],
        )

        self.assertContractPeople(
            self.contract1_id,
            owner=self.adopter,
            payer=self.cecilia,
            member=self.adopter,
        )
        self.assertContractPeople(
            self.contract2_id,
            owner=self.cecilia,
            payer=self.cecilia,
            member=self.cecilia,
        )
