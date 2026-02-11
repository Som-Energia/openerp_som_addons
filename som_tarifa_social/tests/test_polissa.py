# -*- coding: utf-8 -*-

from destral import testing


class TestPolissa(testing.OOTestCaseWithCursor):
    def setUp(self):
        self.pp_obj = self.openerp.pool.get("product.pricelist")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        super(TestPolissa, self).setUp()

        # Tarifes normals
        self.pp_periodes_peninsula_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        )[1]
        self.pp_periodes_insular_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]
        self.pp_indexada_peninsula_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_peninsula"
        )[1]
        self.pp_indexada_balears_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_balears"
        )[1]
        self.pp_indexada_canaries_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_canaries"
        )[1]

        # Tarifes socials
        self.pp_social_periodes_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "www_som", "tarifa_20TD_SOM_SOCIAL"
        )[1]
        self.pp_social_periodes_insular_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "www_som", "tarifa_20TD_SOM_INSULAR_SOCIAL"
        )[1]
        self.pp_social_indexada_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "www_som", "tarifa_indexada_20TD_peninsula_social"
        )[1]
        self.pp_social_indexada_balears_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "www_som", "tarifa_indexada_20TD_balears_social"
        )[1]
        self.pp_social_indexada_canaries_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "www_som", "tarifa_indexada_20TD_canaries_social"
        )[1]

        self.tarifa = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'tarifa_20TD'
        )[1]

    def test_get_new_tariff_change_social_or_regular__to_social(self):
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_tarifa_018"
        )[1]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            'llista_preu': self.pp_periodes_peninsula_id,
            'tarifa': self.tarifa,
            'mode_facturacio': 'atr',
        })
        self.pol_obj.send_signal(self.cursor, self.uid, [pol_id], ['validar', 'contracte'])
        change_type = "to_social"

        result = self.pol_obj.get_new_tariff_change_social_or_regular(
            self.cursor, self.uid, pol_id, change_type, context=None
        )

        pol = self.pol_obj.browse(self.cursor, self.uid, pol_id)
        expected_mapping = {
            self.pp_periodes_peninsula_id: self.pp_social_periodes_id,
            self.pp_periodes_insular_id: self.pp_social_periodes_insular_id,
            self.pp_indexada_peninsula_id: self.pp_social_indexada_id,
            self.pp_indexada_balears_id: self.pp_social_indexada_balears_id,
            self.pp_indexada_canaries_id: self.pp_social_indexada_canaries_id,
        }
        expected_result = expected_mapping[pol.llista_preu.id]
        self.assertEqual(result, expected_result)

    def test_get_new_tariff_change_social_or_regular__to_regular(self):
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_tarifa_018"
        )[1]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            'llista_preu': self.pp_social_periodes_id,
            'tarifa': self.tarifa,
            'mode_facturacio': 'atr',
        })
        self.pol_obj.send_signal(self.cursor, self.uid, [pol_id], ['validar', 'contracte'])
        change_type = "to_regular"

        result = self.pol_obj.get_new_tariff_change_social_or_regular(
            self.cursor, self.uid, pol_id, change_type, context=None
        )

        self.assertEqual(result, self.pp_periodes_peninsula_id)

    def test_get_new_tariff_change_social_or_regular__invalid_change(self):
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_tarifa_018"
        )[1]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            'llista_preu': self.pp_periodes_peninsula_id,
            'tarifa': self.tarifa,
            'mode_facturacio': 'atr',
        })
        self.pol_obj.send_signal(self.cursor, self.uid, [pol_id], ['validar', 'contracte'])
        change_type = "invalid_change"

        with self.assertRaises(Exception) as context:
            self.pol_obj.get_new_tariff_change_social_or_regular(
                self.cursor, self.uid, pol_id, change_type, context=None
            )

        self.assertTrue('Cannot change {} tariff'.format(change_type) in str(context.exception))

    def test_get_new_tariff_change_social_or_regular__invalid_from_invalid_tariff(self):
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_tarifa_018"
        )[1]
        other_pricelist_id = self.pp_obj.search(
            self.cursor, self.uid, [('name', '=', 'TARIFAS ELECTRICIDAD')])[0]
        self.pol_obj.write(self.cursor, self.uid, pol_id, {
            'llista_preu': other_pricelist_id,
            'tarifa': self.tarifa,
            'mode_facturacio': 'atr',
        })
        self.pol_obj.send_signal(self.cursor, self.uid, [pol_id], ['validar', 'contracte'])
        change_type = "to_social"

        with self.assertRaises(Exception) as context:
            self.pol_obj.get_new_tariff_change_social_or_regular(
                self.cursor, self.uid, pol_id, change_type, context=None
            )

        self.assertTrue('Cannot change {} tariff'.format(change_type) in str(context.exception))
