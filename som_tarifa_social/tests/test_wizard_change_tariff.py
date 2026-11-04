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

    def _prepare_contract(self, pricelist_id):
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            "llista_preu": pricelist_id,
            "tarifa": self.tarifa,
            "mode_facturacio": "atr",
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
