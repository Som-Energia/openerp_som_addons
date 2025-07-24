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
        self.openerp.pool.get('som.sortida.state')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol = pol_obj.browse(cursor, uid, polissa_id)
        # Check initial state
        self.assertEqual(
            pol.sortida_state_id.name, 'Contrate sense sòcia',
            "L'estat inicial hauria de ser 'Contrate sense sòcia' en comptes de {}".format(
                pol.sortida_state_id.name
            ))

    def tests_gicedata_polissa_history(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        hist_obj = self.openerp.pool.get('som.sortida.history')
        pol_obj = self.openerp.pool.get('giscedata.polissa')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol_obj.write(cursor, uid, polissa_id, {'soci': False})
        hist_id = hist_obj.search(cursor, uid, [('polissa_id', '=', polissa_id)])
        self.assertTrue(hist_id, "No s'ha trobat cap historial per a la pòlissa")

        hist_data = hist_obj.read(cursor, uid, hist_id, ['polissa_id'])
        self.assertEqual(hist_data[0]['polissa_id'][0], polissa_id,
                         "L'historial hauria de correspondre a la pòlissa correcta")
