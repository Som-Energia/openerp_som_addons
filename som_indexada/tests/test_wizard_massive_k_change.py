# -*- coding: utf-8 -*-
from __future__ import absolute_import
import base64
import mock
from destral.testing import TestCase
from destral.transaction import Transaction


class TestMassiveKChange(TestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool
        self.polissa_obj = self.pool.get("giscedata.polissa")
        self.wizard_obj = self.pool.get("wizard.massive.k.change")
        imd = self.pool.get("ir.model.data")
        self.polissa_id = imd.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.social_category_id = imd.get_object_reference(
            self.cursor, self.uid, "som_indexada", "category_tarifa_social"
        )[1]
        self.other_category_id = imd.get_object_reference(
            self.cursor, self.uid, "som_indexada", "category_indexada_prova_pilot"
        )[1]
        self.polissa_obj.write(self.cursor, self.uid, self.polissa_id, {
            "mode_facturacio": "index",
            "category_id": [(6, 0, [self.other_category_id])],
        })

    def tearDown(self):
        self.txn.stop()

    def activate_polissa(self):
        self.polissa_obj.send_signal(
            self.cursor, self.uid, [self.polissa_id], ["validar", "contracte"]
        )

    def change_k(self, social_tariff=None, modcon_actual=False):
        vals = {
            "csv_file": base64.b64encode(b"contracte,coeficient_k\n0018,10\n"),
            "pending_modcon": True,
            "modcon_actual": modcon_actual,
        }
        if social_tariff is not None:
            vals["social_tariff"] = social_tariff
        wiz_id = self.wizard_obj.create(self.cursor, self.uid, vals)
        self.wizard_obj.change_k_from_csv(self.cursor, self.uid, [wiz_id])
        return self.wizard_obj.read(self.cursor, self.uid, wiz_id, ["info", "social_tariff"])

    def categories(self):
        return self.polissa_obj.read(
            self.cursor, self.uid, self.polissa_id, ["category_id"]
        )["category_id"]

    def test_social_tariff_adds_category_preserving_existing(self):
        self.activate_polissa()
        result = self.change_k(social_tariff=True)
        self.assertEqual(result["info"], u"Procés acabat correctament!")
        self.assertEqual(set(self.categories()), {
            self.other_category_id, self.social_category_id,
        })
        polissa = self.polissa_obj.browse(self.cursor, self.uid, self.polissa_id)
        self.assertEqual(polissa.modcontractuals_ids[0].coeficient_k, 10)

    def test_social_tariff_with_current_modcon(self):
        self.activate_polissa()
        result = self.change_k(social_tariff=True, modcon_actual=True)
        self.assertEqual(result["info"], u"Procés acabat correctament!")
        self.assertIn(self.social_category_id, self.categories())

    def test_unchecked_by_default_does_not_add_category(self):
        self.activate_polissa()
        result = self.change_k()
        self.assertFalse(result["social_tariff"])
        self.assertEqual(result["info"], u"Procés acabat correctament!")
        self.assertEqual(self.categories(), [self.other_category_id])

    def test_unchecked_does_not_remove_social_category(self):
        self.activate_polissa()
        self.polissa_obj.write(self.cursor, self.uid, self.polissa_id, {
            "category_id": [(4, self.social_category_id)],
        })
        result = self.change_k(social_tariff=False)
        self.assertEqual(result["info"], u"Procés acabat correctament!")
        self.assertIn(self.social_category_id, self.categories())

    def test_existing_social_category_is_not_duplicated(self):
        self.activate_polissa()
        self.polissa_obj.write(self.cursor, self.uid, self.polissa_id, {
            "category_id": [(4, self.social_category_id)],
        })
        result = self.change_k(social_tariff=True)
        self.assertEqual(result["info"], u"Procés acabat correctament!")
        self.assertEqual(self.categories().count(self.social_category_id), 1)

    def test_inactive_polissa_does_not_receive_category(self):
        result = self.change_k(social_tariff=True)
        self.assertIn(u"han fallat", result["info"])
        self.assertEqual(self.categories(), [self.other_category_id])

    def test_pending_modcon_does_not_receive_category(self):
        self.activate_polissa()
        self.change_k()
        result = self.change_k(social_tariff=True)
        self.assertIn(u"han fallat", result["info"])
        self.assertEqual(self.categories(), [self.other_category_id])

    def test_failed_modcon_does_not_receive_category(self):
        self.activate_polissa()
        contract_wizard = self.pool.get("giscedata.polissa.crear.contracte")
        with mock.patch.object(
            type(contract_wizard), "action_crear_contracte", side_effect=Exception("Test failure")
        ):
            result = self.change_k(social_tariff=True)
        self.assertIn(u"han fallat", result["info"])
        self.assertEqual(self.categories(), [self.other_category_id])
