# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing


class TestWizardChangeTariff(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestWizardChangeTariff, self).setUp()
        self.pp_obj = self.openerp.pool.get("product.pricelist")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.wiz_obj = self.openerp.pool.get("wizard.change.tariff.social")
        self.modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")

        self.pp_periodes_regular_id = self._pricelist_id("2.0TD_SOM")
        self.pp_social_periodes_id = self._pricelist_id("2.0TD_SOM_SOCIAL")
        self.tarifa = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "tarifa_20TD"
        )[1]

    def _pricelist_id(self, name):
        return self.pp_obj.search(
            self.cursor, self.uid, [("name", "=", name)]
        )[0]

    def _prepare_contract(self, pricelist_id, mode_facturacio="atr"):
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            "llista_preu": pricelist_id,
            "tarifa": self.tarifa,
            "mode_facturacio": mode_facturacio,
            "mode_facturacio_generacio": mode_facturacio,
        })
        self.pol_obj.send_signal(
            self.cursor, self.uid, [pol_id], ["validar", "contracte"]
        )
        return pol_id

    def _change_tariff(self, pol_id, change_type):
        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {
            "polissa_id": pol_id,
        })
        wizard = self.wiz_obj.browse(self.cursor, self.uid, wiz_id)
        return wizard.change_tariff(
            change_type=change_type, context={"active_id": pol_id}
        )

    def test_change_to_social_creates_contract_modification(self):
        pol_id = self._prepare_contract(self.pp_periodes_regular_id)

        modcon_id = self._change_tariff(pol_id, "to_social")

        modcon = self.modcon_obj.browse(self.cursor, self.uid, modcon_id)
        self.assertEqual(modcon.llista_preu.id, self.pp_social_periodes_id)

    def test_change_to_regular_creates_contract_modification(self):
        pol_id = self._prepare_contract(self.pp_social_periodes_id)
        pp_regular_id = self.pp_periodes_regular_id

        modcon_id = self._change_tariff(pol_id, "to_regular")

        modcon = self.modcon_obj.browse(self.cursor, self.uid, modcon_id)
        self.assertEqual(modcon.llista_preu.id, pp_regular_id)

    def test_category_changes_only_when_modification_is_applied(self):
        category_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social", "categ_tarifa_social",
        )[1]
        other_id = self.openerp.pool.get("giscedata.polissa.category").create(
            self.cursor, self.uid, {"name": "Other category", "code": "OTHER"},
        )
        pol_id = self._prepare_contract(self.pp_periodes_regular_id)
        self.pol_obj.write(self.cursor, self.uid, [pol_id], {
            "category_id": [(4, other_id)],
        })
        modcon_id = self._change_tariff(pol_id, "to_social")
        categories = self.pol_obj.read(
            self.cursor, self.uid, pol_id, ["category_id"]
        )["category_id"]
        self.assertNotIn(category_id, categories)
        self.assertIn(other_id, categories)

        self.modcon_obj.aplicar_modificacio(self.cursor, self.uid, modcon_id)
        categories = self.pol_obj.read(
            self.cursor, self.uid, pol_id, ["category_id"]
        )["category_id"]
        self.assertIn(category_id, categories)
        self.assertIn(other_id, categories)

    def test_category_removed_when_regular_modification_is_applied(self):
        category_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social", "categ_tarifa_social",
        )[1]
        other_id = self.openerp.pool.get("giscedata.polissa.category").create(
            self.cursor, self.uid, {"name": "Other category", "code": "OTHER"},
        )
        pol_id = self._prepare_contract(self.pp_social_periodes_id)
        self.pol_obj.write(self.cursor, self.uid, [pol_id], {
            "category_id": [(4, category_id), (4, other_id)],
        })
        modcon_id = self._change_tariff(pol_id, "to_regular")
        categories = self.pol_obj.read(
            self.cursor, self.uid, pol_id, ["category_id"]
        )["category_id"]
        self.assertIn(category_id, categories)
        self.assertIn(other_id, categories)

        self.modcon_obj.aplicar_modificacio(self.cursor, self.uid, modcon_id)
        categories = self.pol_obj.read(
            self.cursor, self.uid, pol_id, ["category_id"]
        )["category_id"]
        self.assertNotIn(category_id, categories)
        self.assertIn(other_id, categories)

    def test_change_indexed_to_social_uses_invoicing_code(self):
        regular_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada",
            "pricelist_indexada_20td_peninsula_2024",
        )[1]
        social_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social",
            "tarifa_indexada_20TD_peninsula_social",
        )[1]
        pol_id = self._prepare_contract(regular_id, "index")

        modcon_id = self._change_tariff(pol_id, "to_social")

        modcon = self.modcon_obj.browse(self.cursor, self.uid, modcon_id)
        self.assertEqual(modcon.llista_preu.id, social_id)
        self.assertEqual(modcon.mode_facturacio, "index")
        self.assertEqual(modcon.mode_facturacio_generacio, "index")

    def test_change_indexed_to_regular_uses_invoicing_code(self):
        regular_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada",
            "pricelist_indexada_20td_peninsula_2024",
        )[1]
        social_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social",
            "tarifa_indexada_20TD_peninsula_social",
        )[1]
        pol_id = self._prepare_contract(social_id, "index")

        modcon_id = self._change_tariff(pol_id, "to_regular")

        modcon = self.modcon_obj.browse(self.cursor, self.uid, modcon_id)
        self.assertEqual(modcon.llista_preu.id, regular_id)
        self.assertEqual(modcon.mode_facturacio, "index")
        self.assertEqual(modcon.mode_facturacio_generacio, "index")
