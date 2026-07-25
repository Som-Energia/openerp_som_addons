# -*- coding: utf-8 -*-
from destral import testing


class TestWizardChangeTariff(testing.OOTestCaseWithCursor):

    def setUp(self):
        self.pp_obj = self.openerp.pool.get("product.pricelist")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.wiz_obj = self.openerp.pool.get("wizard.change.tariff.social")
        self.modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        super(TestWizardChangeTariff, self).setUp()

        # Tarifes normals
        self.pp_periodes_regular_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', '2.0TD_SOM')])[0]
        self.pp_periodes_insular_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', '2.0TD_SOM_INSULAR')])[0]
        self.pp_indexada_peninsula_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', 'Indexada 2.0TD Península')])[0]
        self.pp_indexada_balears_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', 'Indexada 2.0TD Balears')])[0]
        self.pp_indexada_canaries_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', 'Indexada 2.0TD Canàries')])[0]

        # Tarifes socials
        self.pp_social_periodes_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', '2.0TD_SOM_SOCIAL')])[0]
        self.pp_social_indexada_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', '2.Indexada 2.0TD Península SOCIAL')])[0]

        self.tarifa = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'tarifa_20TD'
        )[1]

    def test_wizard_change_tariff_social__to_social(self):
        cursor = self.cursor
        uid = self.uid
        pol_id = self.imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', "polissa_tarifa_018"
        )[1]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            'llista_preu': self.pp_periodes_regular_id,
            'tarifa': self.tarifa,
            'mode_facturacio': 'atr',
        })
        self.pol_obj.send_signal(cursor, uid, [pol_id], ['validar', 'contracte'])
        pp_id = self.pp_obj.search(cursor, uid, [('name', '=', '2.0TD_SOM_SOCIAL')])[0]
        wiz_id = self.wiz_obj.create(cursor, uid, {
            'pricelist_id': pp_id,
            'polissa_id': pol_id,
        })
        wiz = self.wiz_obj.browse(cursor, uid, wiz_id)
        pol = self.pol_obj.browse(cursor, uid, pol_id)
        self.assertNotEqual(pol.llista_preu.id, pp_id)

        mod_contractual_id = wiz.change_tariff(
            change_type='to_social', context={'active_id': pol_id})

        mod = self.modcon_obj.browse(cursor, uid, mod_contractual_id)
        self.assertEqual(mod.llista_preu.id, pp_id)

    def test_wizard_change_tariff_social__to_regular(self):
        cursor = self.cursor
        uid = self.uid
        pol_id = self.imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', "polissa_tarifa_018"
        )[1]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            'llista_preu': self.pp_social_periodes_id,
            'tarifa': self.tarifa,
            'mode_facturacio': 'atr',
        })
        self.pol_obj.send_signal(cursor, uid, [pol_id], ['validar', 'contracte'])
        pp_id = self.pp_obj.search(cursor, uid, [('name', '=', '2.0TD_SOM')])[0]
        wiz_id = self.wiz_obj.create(cursor, uid, {
            'pricelist_id': pp_id,
            'polissa_id': pol_id,
        })
        wiz = self.wiz_obj.browse(cursor, uid, wiz_id)
        pol = self.pol_obj.browse(cursor, uid, pol_id)
        self.assertTrue(pol.llista_preu.id != pp_id)

        mod_contractual_id = wiz.change_tariff(
            change_type='to_regular', context={'active_id': pol_id})

        mod = self.modcon_obj.browse(cursor, uid, mod_contractual_id)
        self.assertEqual(mod.llista_preu.id, pp_id)
