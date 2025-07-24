# -*- coding: utf-8 -*-
from destral import testing


class TestsGiscedataPolissa(testing.OOTestCaseWithCursor):
    def test_giscedata_polissa_te_socia_real_vinculada(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol = pol_obj.browse(cursor, uid, polissa_id)
        self.assertFalse(pol.te_socia_real_vinculada,
                         "La pòlissa no hauria de tenir sòcia real vinculada")

        soci_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'soci_0001'
        )[1]
        pol_obj.write(cursor, uid, [polissa_id], {'soci': soci_id})
        pol = pol_obj.browse(cursor, uid, polissa_id)
        self.assertTrue(pol.te_socia_real_vinculada,
                        "La pòlissa hauria de ser amb sòcia real vinculada")

    def test_giscedata_polissa_sortida_state(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        state_obj = self.openerp.pool.get('som.sortida.state')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol = pol_obj.browse(cursor, uid, polissa_id)
        # Check initial state
        self.assertEqual(pol.sortida_state_id.name, 'Correcte',
                         "L'estat inicial hauria de ser 'Correcte'")

        # Change state
        new_state_id = state_obj.search(cursor, uid, [('name', '=', 'En procés')], limit=1)[0]
        pol_obj.write(cursor, uid, [polissa_id], {'sortida_state_id': new_state_id})
        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.name, 'En procés',
                         "L'estat hauria de ser 'En procés'")
