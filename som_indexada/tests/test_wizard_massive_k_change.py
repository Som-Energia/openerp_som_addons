# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date, timedelta
import base64
import mock

from destral.transaction import Transaction
from giscedata_switching.tests.common_tests import TestSwitchingImport


class TestMassiveKChange(TestSwitchingImport):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool
        self.polissa_obj = self.pool.get("giscedata.polissa")
        self.wizard_obj = self.pool.get("wizard.massive.k.change")
        imd_obj = self.pool.get("ir.model.data")
        self.polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.category_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "category_tarifa_social"
        )[1]
        self.existing_category_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "category_indexada_prova_pilot"
        )[1]

    def tearDown(self):
        self.txn.stop()

    def open_polissa(self):
        self.polissa_obj.send_signal(
            self.cursor, self.uid, [self.polissa_id], ["validar", "contracte"]
        )
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id, {"mode_facturacio": "index"}
        )

    def create_wizard(self, **values):
        polissa_name = self.polissa_obj.read(
            self.cursor, self.uid, self.polissa_id, ["name"]
        )["name"]
        csv_file = "name,coeficient_k\n{},1\n".format(polissa_name)
        params = {"csv_file": base64.b64encode(csv_file.encode("utf-8"))}
        params.update(values)
        return self.wizard_obj.create(self.cursor, self.uid, params)

    def get_categories(self):
        return self.polissa_obj.read(
            self.cursor, self.uid, self.polissa_id, ["category_id"]
        )["category_id"]

    def change_k(self, **values):
        wizard_id = self.create_wizard(**values)
        self.wizard_obj.change_k_from_csv(self.cursor, self.uid, [wizard_id])
        return self.wizard_obj.read(self.cursor, self.uid, wizard_id, ["info"])["info"]

    def test_social_tariff_is_unchecked_by_default(self):
        wizard_id = self.create_wizard()
        wizard = self.wizard_obj.read(
            self.cursor, self.uid, wizard_id, ["social_tariff"]
        )
        self.assertFalse(wizard["social_tariff"])

    def test_category_is_active(self):
        category = self.pool.get("giscedata.polissa.category").read(
            self.cursor, self.uid, self.category_id, ["name", "active", "code"]
        )
        self.assertEqual(category["name"], "Tarifa social")
        self.assertTrue(category["active"])
        self.assertEqual(category["code"], "TS")

    def test_checked_adds_category_and_preserves_existing_categories(self):
        self.open_polissa()
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id,
            {"category_id": [(4, self.existing_category_id)]},
        )
        before = set(self.get_categories())
        info = self.change_k(social_tariff=True)
        self.assertEqual(info, u"Procés acabat correctament!")
        self.assertEqual(set(self.get_categories()), before | set([self.category_id]))

    def test_unchecked_keeps_existing_social_tariff_category(self):
        self.open_polissa()
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id,
            {"category_id": [(4, self.category_id), (4, self.existing_category_id)]},
        )
        before = set(self.get_categories())
        info = self.change_k()
        self.assertEqual(info, u"Procés acabat correctament!")
        self.assertEqual(set(self.get_categories()), before)

    def test_unchecked_does_not_add_social_tariff_category(self):
        self.open_polissa()
        before = set(self.get_categories())
        info = self.change_k()
        self.assertEqual(info, u"Procés acabat correctament!")
        self.assertEqual(set(self.get_categories()), before)
        self.assertNotIn(self.category_id, self.get_categories())

    def test_checked_does_not_duplicate_existing_category(self):
        self.open_polissa()
        self.polissa_obj.write(
            self.cursor, self.uid, self.polissa_id,
            {"category_id": [(4, self.category_id)]},
        )
        info = self.change_k(social_tariff=True)
        self.assertEqual(info, u"Procés acabat correctament!")
        self.assertEqual(self.get_categories().count(self.category_id), 1)

    def test_inactive_policy_does_not_receive_category(self):
        before = set(self.get_categories())
        info = self.change_k(social_tariff=True)
        self.assertIn(u"han fallat", info)
        self.assertEqual(set(self.get_categories()), before)

    def test_pending_modcon_adds_category_after_success(self):
        self.open_polissa()
        info = self.change_k(social_tariff=True, pending_modcon=True)
        self.assertEqual(info, u"Procés acabat correctament!")
        self.assertIn(self.category_id, self.get_categories())
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)
        self.assertEqual(polissa.modcontractuals_ids[0].state, "pendent")
        self.assertEqual(
            polissa.modcontractuals_ids[0].data_inici,
            str(date.today() + timedelta(days=1)),
        )

    def test_modcon_actual_adds_category_after_success(self):
        self.open_polissa()
        info = self.change_k(social_tariff=True, modcon_actual=True)
        self.assertEqual(info, u"Procés acabat correctament!")
        self.assertIn(self.category_id, self.get_categories())

    @mock.patch(
        "giscedata_polissa.wizard.wizard_crear_contracte."
        "GiscedataPolissaCrearContracte.action_crear_contracte",
        side_effect=Exception("Contract creation failed"),
    )
    def test_failed_contract_creation_does_not_receive_category(self, create_contract):
        self.open_polissa()
        before = set(self.get_categories())
        info = self.change_k(social_tariff=True)
        self.assertEqual(create_contract.call_count, 1)
        self.assertIn(u"han fallat", info)
        self.assertEqual(set(self.get_categories()), before)
