# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import xml.etree.ElementTree as ET
from datetime import datetime

from osv import fields
from osv.osv import except_osv

from .. import res_partner, giscedata_polissa
import mock


class TestPolissaAdministradora(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @mock.patch.object(res_partner.ResPartner, "search")
    def test_create_contract_administrator__exception(self, mock_function):
        mock_function.return_value = [1]
        res_partner_obj = self.model("res.partner")

        partner_values = {
            "name": "Test",
            "vat": "ES12345678Z",
            "lang": "en_US",
            "email": "test@test.com",
            "comercial": "webforms",
        }

        with self.assertRaises(except_osv):
            res_partner_obj.create_contract_administrator(
                self.cursor, self.uid, partner_values, context={}
            )

    def test_create_contract_administrator(self):
        res_partner_obj = self.model("res.partner")
        imd_obj = self.model("ir.model.data")
        admin_cat = imd_obj._get_obj(
            self.cursor,
            self.uid,
            "som_polissa_administradora",
            "res_partner_category_administradora",
        )

        partner_values = {
            "name": "Test",
            "vat": "ES12345678Z",
            "lang": "en_US",
            "email": "test@test.com",
            "comercial": "webforms",
        }

        new_partner_id = res_partner_obj.create_contract_administrator(
            self.cursor, self.uid, partner_values, context={}
        )

        new_partner = res_partner_obj.browse(self.cursor, self.uid, new_partner_id)
        self.assertEqual(partner_values["name"], new_partner.name)
        self.assertEqual(partner_values["vat"], new_partner.vat)
        self.assertEqual(partner_values["lang"], new_partner.lang)
        self.assertEqual(partner_values["comercial"], new_partner.comercial)
        self.assertIn(admin_cat, new_partner.category_id)
        self.assertTrue(new_partner.ref)
        self.assertTrue(new_partner.ref.startswith("A"))

    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "validate_partner")
    def test_add_contract_administrator__polissa_invalid_partner(self, mock_validate_partner):
        pol_obj = self.model("giscedata.polissa")
        res_partner_obj = self.model("res.partner")

        partner_id = 1
        polissa_id = 1
        is_representative = True
        permissions = "manage"

        def validate_partner(cursor, uid, partner_id):
            return {"modification": None, "error": "01", "error_msg": ""}

        "res_partner doesn't exists"
        mock_validate_partner.side_effect = validate_partner

        result = pol_obj.add_contract_administrator(
            self.cursor,
            self.uid,
            polissa_id,
            partner_id,
            permissions,
            is_representative,
            context={},
        )

        self.assertEqual(result["error"], "01")

    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "create_modcon")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "read")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "validate_partner")
    def test_add_contract_administrator__polissa_without_administradora(
        self, mock_validate_partner, mock_read_polissa, mock_create_modcon_polissa
    ):
        pol_obj = self.model("giscedata.polissa")
        res_partner_obj = self.model("res.partner")
        admin_mod_obj = self.model("som.admin.modification")

        titular_id = 2
        partner_id = 1
        polissa_id = 1
        is_representative = True
        permissions = "readonly"

        mock_read_polissa.return_value = {"administradora": None, "titular": [titular_id]}
        mock_validate_partner.return_value = {}
        mock_create_modcon_polissa.return_value = {}

        result = pol_obj.add_contract_administrator(
            self.cursor,
            self.uid,
            polissa_id,
            partner_id,
            permissions,
            is_representative,
            context={},
        )

        admin_mod_id = result["modification"]
        admin_mod = admin_mod_obj.browse(self.cursor, self.uid, admin_mod_id)
        self.assertEqual(admin_mod.polissa_id.id, polissa_id)
        self.assertEqual(admin_mod.old_administradora.id, False)
        self.assertEqual(admin_mod.new_administradora.id, partner_id)
        self.assertEqual(admin_mod.permissions, permissions)
        self.assertEqual(admin_mod.is_legal_representative, is_representative)

        titular = res_partner_obj.browse(self.cursor, self.uid, titular_id)
        partner = res_partner_obj.browse(self.cursor, self.uid, partner_id)

        admin_cat = pol_obj.get_admin_cat(self.cursor, self.uid)

        self.assertEqual(admin_cat.id, partner.category_id[0].id)

        pol_obj.create_modcon.assert_called_once_with(
            self.cursor,
            self.uid,
            polissa_id,
            {"administradora": partner_id, "administradora_permissions": permissions},
        )

    @mock.patch.object(res_partner.ResPartner, "read")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "search")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "create_modcon")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "read")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "remove_administrator_category")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "validate_partner")
    def test_add_contract_administrator__polissa_with_administradora(
        self,
        mock_validate_partner,
        mock_remove_administrator_category,
        mock_read_polissa,
        mock_create_modcon_polissa,
        mock_search_polissa,
        mock_read_res_partner,
    ):
        pol_obj = self.model("giscedata.polissa")
        res_partner_obj = self.model("res.partner")
        admin_mod_obj = self.model("som.admin.modification")

        titular_id = 3
        partner_id = 1
        polissa_id = 1
        is_representative = True
        permissions = "manage"
        mock_read_polissa.return_value = {"administradora": [2], "titular": [titular_id]}
        mock_search_polissa.return_value = {"administradora": [2]}
        admin_cat = pol_obj.get_admin_cat(self.cursor, self.uid)
        mock_read_res_partner.return_value = {
            "id": 2,
            "category_id": [(4, admin_cat.id)],
            "name": "Test",
            "vat": "12345678Z",
        }
        mock_validate_partner.return_value = {}

        def remove_administrator_category_mock(cursor, uid, partner_id):
            pass

        mock_remove_administrator_category.side_effect = remove_administrator_category_mock

        def create_modcon_polissa_mock(cursor, uid, polissa_id, vals):
            return {}

        mock_create_modcon_polissa.side_effect = create_modcon_polissa_mock

        result = pol_obj.add_contract_administrator(
            self.cursor,
            self.uid,
            polissa_id,
            partner_id,
            permissions,
            is_representative,
            context={},
        )

        admin_mod_id = result["modification"]
        admin_mod = admin_mod_obj.browse(self.cursor, self.uid, admin_mod_id)
        self.assertEqual(admin_mod.polissa_id.id, polissa_id)
        self.assertEqual(admin_mod.old_administradora.id, 2)
        self.assertEqual(admin_mod.new_administradora.id, partner_id)
        self.assertEqual(admin_mod.permissions, permissions)
        self.assertEqual(admin_mod.is_legal_representative, is_representative)

        pol_obj.remove_administrator_category.assert_called_once_with(self.cursor, self.uid, 2)

        pol_obj.create_modcon.assert_called_once_with(
            self.cursor,
            self.uid,
            polissa_id,
            {"administradora": partner_id, "administradora_permissions": permissions},
        )

    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "read")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "validate_partner")
    def test_add_contract_administrator__polissa_with_same_administradora(
        self, mock_validate_partner, mock_read_polissa
    ):
        pol_obj = self.model("giscedata.polissa")

        partner_id = 1
        polissa_id = 1
        is_representative = True
        permissions = "manage"
        mock_read_polissa.return_value = {"administradora": [1, "Pepito"]}
        mock_validate_partner.return_value = {}

        result = pol_obj.add_contract_administrator(
            self.cursor,
            self.uid,
            polissa_id,
            partner_id,
            permissions,
            is_representative,
            context={},
        )

        self.assertEqual(result["error"], "03")

    @mock.patch.object(res_partner.ResPartner, "read")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "create_modcon")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "read")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "remove_administrator_category")
    def test_remove_contract_administrator(
        self,
        mock_remove_administrator_category,
        mock_read_polissa,
        mock_create_modcon_polissa,
        mock_read_res_partner,
    ):
        pol_obj = self.model("giscedata.polissa")
        res_partner_obj = self.model("res.partner")

        partner_id = 1
        polissa_id = 1
        mock_read_polissa.return_value = {"administradora": [1], "titular": [2]}
        admin_cat = pol_obj.get_admin_cat(self.cursor, self.uid)
        mock_read_res_partner.return_value = {"id": 1, "category_id": [(4, admin_cat.id)]}

        def remove_administrator_category_mock(cursor, uid, partner_id):
            pass

        mock_remove_administrator_category.side_effect = remove_administrator_category_mock

        def create_modcon_polissa_mock(cursor, uid, polissa_id, vals):
            return {}

        mock_create_modcon_polissa.side_effect = create_modcon_polissa_mock

        result = pol_obj.remove_contract_administrator(
            self.cursor, self.uid, polissa_id, context={}
        )

        self.assertTrue(result)

        pol_obj.remove_administrator_category.assert_called_once_with(self.cursor, self.uid, 1)

        pol_obj.create_modcon.assert_called_once_with(
            self.cursor,
            self.uid,
            polissa_id,
            {"administradora": None, "administradora_permissions": None},
        )

    def test_add_administrator_category__one_partner(self):
        res_partner_obj = self.model("res.partner")
        imd_obj = self.model("ir.model.data")
        admin_cat = imd_obj._get_obj(
            self.cursor,
            self.uid,
            "som_polissa_administradora",
            "res_partner_category_administradora",
        )
        partner = imd_obj._get_obj(self.cursor, self.uid, "base", "res_partner_2")
        res_partner_obj.add_administrator_category(self.cursor, self.uid, partner.id)

        self.assertIn(admin_cat, partner.category_id)

    def test_add_administrator_category__many_partners(self):
        res_partner_obj = self.model("res.partner")
        imd_obj = self.model("ir.model.data")
        admin_cat = imd_obj._get_obj(
            self.cursor,
            self.uid,
            "som_polissa_administradora",
            "res_partner_category_administradora",
        )

        partner_1 = imd_obj._get_obj(self.cursor, self.uid, "base", "res_partner_2")
        partner_2 = imd_obj._get_obj(self.cursor, self.uid, "base", "res_partner_3")

        res_partner_obj.add_administrator_category(
            self.cursor, self.uid, [partner_1.id, partner_2.id]
        )

        self.assertIn(admin_cat, partner_1.category_id)
        self.assertIn(admin_cat, partner_2.category_id)

    @mock.patch.object(res_partner.ResPartner, "write")
    @mock.patch.object(res_partner.ResPartner, "read")
    def test_become_owner__admin_to_owner(self, mock_res_partner_read, mock_res_partner_write):
        pol_obj = self.model("giscedata.polissa")
        res_partner_obj = self.model("res.partner")

        partner_id = 1

        admin_cat = pol_obj.get_admin_cat(self.cursor, self.uid)
        mock_res_partner_read.return_value = {
            "id": partner_id,
            "category_id": [admin_cat.id],
            "ref": "A000001",
        }

        res_partner_obj.become_owner(self.cursor, self.uid, 1)

        expected_vals = {"ref": "T000001"}
        mock_res_partner_write.assert_called_once_with(
            self.cursor, self.uid, partner_id, expected_vals
        )

    @mock.patch.object(res_partner.ResPartner, "write")
    @mock.patch.object(res_partner.ResPartner, "read")
    def test_become_owner__member_to_owner(self, mock_res_partner_read, mock_res_partner_write):
        pol_obj = self.model("giscedata.polissa")
        res_partner_obj = self.model("res.partner")

        partner_id = 1

        imd_obj = self.model("ir.model.data")
        soci_cat = imd_obj._get_obj(
            self.cursor, self.uid, "som_partner_account", "res_partner_category_soci"
        )

        mock_res_partner_read.return_value = {
            "id": partner_id,
            "category_id": [soci_cat.id],
            "ref": "S000001",
        }

        with self.assertRaises(except_osv):
            res_partner_obj.become_owner(self.cursor, self.uid, 1)
