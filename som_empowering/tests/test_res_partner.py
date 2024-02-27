from destral import testing
import unittest
import mock
import pymongo
from destral.transaction import Transaction
from yamlns import ns


class ResPartnerTest(testing.OOTestCase):
    def get_reference(self, semantic_id):
        return self.IrModelData.get_object_reference(
            self.cursor, self.uid, *semantic_id.split(".")
        )[1]

    from yamlns.testutils import assertNsEqual

    def setUp(self):
        self.maxDiff = None
        self.databasename = "som_empowering_test"
        c = pymongo.MongoClient()
        c.drop_database(self.databasename)
        self.db = c[self.databasename]

        patcher = mock.patch("mongodb_backend.mongodb2.mdbpool.get_db")
        self.get_db_mock = patcher.start()
        self.get_db_mock.return_value = self.db
        self.addCleanup(patcher.stop)

        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.addCleanup(self.txn.stop)

        self.pool = self.openerp.pool
        self.IrModelData = self.pool.get("ir.model.data")
        self.ResPartner = self.pool.get("res.partner")
        self.ResPartnerAddress = self.pool.get("res.partner.address")
        self.GiscedataPolissa = self.pool.get("giscedata.polissa")

        self.contract1 = self.get_reference("giscedata_polissa.polissa_gisce")
        self.owner1 = self.get_reference("base.res_partner_gisce")
        # owner1 is also payer of contract1
        self.notified1 = self.get_reference("base.res_partner_9")

        self.contract2 = self.get_reference("giscedata_polissa.polissa_0001")
        self.owner2 = self.get_reference("base.res_partner_c2c")
        self.payer2 = self.get_reference("base.res_partner_agrolait")
        # payer2 is also notified of contract2

    def tearDown(self):
        c = pymongo.MongoClient()
        c.drop_database(self.databasename)

    def related_contracts(self, partner_id, relations):
        return self.ResPartner.related_contracts(self.cursor, self.uid, partner_id, relations)

    def set_role(self, contract1, partner_id, role):
        self.GiscedataPolissa.write(
            self.cursor,
            self.uid,
            contract1,
            {
                role: partner_id,
            },
        )

    def assertRelated(self, contract1, partner_id, *relations):
        # Comparing the full list of related contracts would be fragile
        self.assertIn(contract1, self.related_contracts(partner_id, relations))

    def assertUnrelated(self, contract1, partner_id, *relations):
        # Comparing the full list of related contracts would be fragile
        self.assertNotIn(contract1, self.related_contracts(partner_id, relations))

    def getRoles(self, contract):
        def getid(foreignkey):
            if not foreignkey:
                return None
            return foreignkey[0]

        polissa = self.GiscedataPolissa.read(self.cursor, self.uid, contract)
        result = ns(
            owner=getid(polissa["titular"]),
            payer=getid(polissa["pagador"]),
            # admin=getid(polissa['administradora']),
            notified=None,
        )
        notify_address = getid(polissa["direccio_notificacio"])
        if notify_address:
            address = self.ResPartnerAddress.read(self.cursor, self.uid, notify_address)
            result.notified = getid(address["partner_id"])

        return result

    def test_fixtures(self):
        "This tests checks assumptions the other tests do on the fixtures"
        self.assertNsEqual(
            ns(
                contract1=self.getRoles(self.contract1),
                contract2=self.getRoles(self.contract2),
            ),
            ns(
                contract1=ns(
                    owner=self.owner1,
                    payer=self.owner1,
                    notified=self.notified1,
                ),
                contract2=ns(
                    owner=self.owner2,
                    payer=self.payer2,
                    notified=self.payer2,
                ),
            ),
        )

    # partner.related_contracts

    def test_related_contracts__titular(self):
        # Contract is just in the related of the owner
        self.assertRelated(self.contract1, self.owner1, "titular")
        self.assertUnrelated(self.contract1, self.owner2, "titular")
        self.assertRelated(self.contract2, self.owner2, "titular")
        self.assertUnrelated(self.contract2, self.payer2, "titular")

    def test_related_contracts__pagador(self):
        # owner2 is not payer of contract 2
        self.assertUnrelated(self.contract2, self.owner2, "pagador")
        # payer2 is
        self.assertRelated(self.contract2, self.payer2, "pagador")
        # but if we set owner2 as the payer of contract2
        self.set_role(self.contract2, self.owner2, "pagador")
        # The situation is inverted
        self.assertRelated(self.contract2, self.owner2, "pagador")
        self.assertUnrelated(self.contract2, self.payer2, "pagador")

    def test_related_contracts__notifica(self):
        # payer2 is both payer but also notifier of contract2
        self.assertRelated(self.contract2, self.payer2, "notifica")
        # but has no relation with contract1
        self.assertUnrelated(self.contract1, self.payer2, "notifica")
        # owner1 is not notified of contrac1
        self.assertUnrelated(self.contract1, self.owner1, "notifica")
        # notified1 is
        self.assertRelated(self.contract1, self.notified1, "notifica")

    @unittest.skip("Missing dependency")
    def test_related_contracts__administrador(self):
        self.assertUnrelated(self.contract1, self.payer2, "administradora")
        self.set_role(self.contract1, self.payer2, "administradora")
        self.assertRelated(self.contract1, self.payer2, "administradora")

    def test_related_contracts__multiple_roles(self):
        # Both owner2 and payer2 are related to c2 with one of those roles
        self.assertRelated(self.contract2, self.owner2, "titular", "pagador")
        self.assertRelated(self.contract2, self.payer2, "titular", "pagador")
        # Neither role is taken by owner1
        self.assertUnrelated(self.contract2, self.owner1, "titular", "pagador")
        # Neither role is taken by notified1 in c1
        self.assertUnrelated(self.contract1, self.notified1, "titular", "pagador")

    def get_token(self, partner):
        return self.ResPartner.read(self.cursor, self.uid, partner, ["empowering_token"])[
            "empowering_token"
        ]

    def token_contracts(self, token):
        result = [ns(x, _id=str(x["_id"])) for x in self.db.tokens.find({"token": token})]
        self.assertEqual(len(result), 1)
        return result[0]["allowed_contracts"]

    def name_and_cups(self, contract_id):
        contract = self.GiscedataPolissa.read(self.cursor, self.uid, contract_id, ["name", "cups"])
        return dict(
            name=contract["name"],
            cups=contract["cups"][1],
        )

    # partner.assign_token

    def test_assign_token__beforeAssigningOne(self):
        token = self.get_token(self.owner1)
        self.assertEqual(token, False)

    def test_assign_token__afterAssignment(self):
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        self.assertTrue(token)

    def test_assign_token__simultaneous_assign_different_tokens(self):
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1, self.owner2])
        token1 = self.get_token(self.owner1)
        token2 = self.get_token(self.owner2)
        self.assertNotEqual(token1, token2)

    def test_assign_token__twice_keepsSameToken(self):
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        new_token = self.get_token(self.owner1)
        self.assertEqual(new_token, token)

    def test_assign_token__setsContractList(self):
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        token_contracts = self.token_contracts(token)
        self.assertIn(self.name_and_cups(self.contract1), token_contracts)
        self.assertNotIn(self.name_and_cups(self.contract2), token_contracts)

    def test_assign_token__ifAlreadyThere_updatesContractList(self):
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        self.db.tokens.update({"token": token}, {"$set": {"allowed_contracts": []}})
        token_contracts = self.token_contracts(token)
        self.assertNotIn(self.name_and_cups(self.contract1), token_contracts)

        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        token_contracts = self.token_contracts(token)
        self.assertIn(self.name_and_cups(self.contract1), token_contracts)
        self.assertNotIn(self.name_and_cups(self.contract2), token_contracts)

    def test_assign_token__whenTokenExistsInErpButMongoIsMissing(self):
        # This case is common in testing: in testing, we update postgres
        # data but not mongo documents

        # Given that there is a token in postgress
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        # But there is no token in mongo
        self.db.tokens.delete_many({"token": token})

        # When we reassign the token
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        # Then the token is kept
        token2 = self.get_token(self.owner1)
        self.assertEqual(token, token2)
        # And the mongo token has been regenerate with the proper contracts
        token_contracts = self.token_contracts(token)
        self.assertIn(self.name_and_cups(self.contract1), token_contracts)
        self.assertNotIn(self.name_and_cups(self.contract2), token_contracts)

    # partner.clear_token

    def test_clear_token(self):
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        self.ResPartner.clear_token(self.cursor, self.uid, [self.owner1])
        # Removed from mongo
        with self.assertRaises(AssertionError):
            # expected to raise because length is 0
            self.token_contracts(token)
        # Removed from partner
        token2 = self.get_token(self.owner1)
        self.assertFalse(token2)

    def test_clear_token_twice(self):
        self.ResPartner.assign_token(self.cursor, self.uid, [self.owner1])
        token = self.get_token(self.owner1)
        self.ResPartner.clear_token(self.cursor, self.uid, [self.owner1])
        self.ResPartner.clear_token(self.cursor, self.uid, [self.owner1])
        # Removed from mongo
        with self.assertRaises(AssertionError):
            # expected to raise because length is 0
            self.token_contracts(token)

    # polissa.contract_modified

    def contract_modified_partners(self, ids, **vals):
        return self.GiscedataPolissa._modified_partners(self.cursor, self.uid, ids, vals)

    def test_modified_partners__non_partner_attribute__empty(self):
        result = self.contract_modified_partners(
            self.contract1,
            name="newvalue",
        )
        self.assertItemsEqual(result, [])

    def test_modified_partners__unsetPayer_updatesFormer(self):
        result = self.contract_modified_partners(
            self.contract2,
            pagador=False,
        )
        self.assertItemsEqual(result, [self.payer2])

    def test_modified_partners__unsetOwner_updatesFormer(self):
        result = self.contract_modified_partners(
            self.contract2,
            titular=False,
        )
        self.assertItemsEqual(result, [self.owner2])

    def test_modified_partners__unsetOwnerPayer_updatesFormerBoth(self):
        result = self.contract_modified_partners(
            self.contract2,
            titular=False,
            pagador=False,
        )
        self.assertItemsEqual(result, [self.payer2, self.owner2])

    def test_modified_partners__manyContracts_updatesBoth(self):
        result = self.contract_modified_partners(
            [self.contract1, self.contract2],
            titular=False,
        )
        self.assertItemsEqual(result, [self.owner1, self.owner2])

    def test_modified_partners__newRelated_updated(self):
        result = self.contract_modified_partners(
            self.contract1,
            titular=self.payer2,
        )
        self.assertItemsEqual(result, [self.owner1, self.payer2])

    def test_modified_partners__sameValue_ignored(self):
        result = self.contract_modified_partners(
            self.contract1,
            titular=self.owner1,
        )
        self.assertItemsEqual(result, [])

    def test_modified_partners__previouslyUnrelated(self):
        self.GiscedataPolissa.write(self.cursor, self.uid, self.contract1, dict(titular=False))
        result = self.contract_modified_partners(
            self.contract1,
            titular=self.owner1,
        )
        self.assertItemsEqual(result, [self.owner1])

    def test_modified_partners__duplicatedRemoved(self):
        result = self.contract_modified_partners(
            [self.contract1, self.contract2],
            titular=self.notified1,
            pagador=self.notified1,
        )
        self.assertItemsEqual(result, [self.notified1, self.owner1, self.owner2, self.payer2])
