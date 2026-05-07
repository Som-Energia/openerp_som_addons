# -*- coding: utf-8 -*-
from destral import testing
from datetime import date, timedelta


class TestsModContractual(testing.OOTestCaseWithCursor):

    def test_renovar_modcontractual(self):
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        modcon_obj = self.openerp.pool.get('giscedata.polissa.modcontractual')
        imd_obj = self.openerp.pool.get("ir.model.data")
        pol_id = imd_obj.get_object_reference(
            self.cursor, 1, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        tarifa_social_id = imd_obj.get_object_reference(
            self.cursor, 1, "www_som", "tarifa_20TD_SOM_INSULAR_SOCIAL"
        )[1]
        pol_obj.send_signal(self.cursor, self.uid, [pol_id], ["validar", "contracte"])
        modcon_ids = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", pol_id)]
        )
        year_ago = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        tommorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        modcon_obj.write(self.cursor, self.uid, [modcon_ids[-1]], {
            'modcon_renovation_type': 'automatic',
            'llista_preu': tarifa_social_id,
            'data_final': tommorrow,
            'data_inici': year_ago,
        })

        modcon_obj.renovar(self.cursor, self.uid, [modcon_ids[-1]])

        modcon_ids_after = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", pol_id)]
        )
        self.assertEqual(len(modcon_ids_after), len(modcon_ids) + 1)
        new_modcon = modcon_obj.browse(
            self.cursor, self.uid, list(set(modcon_ids_after) - set(modcon_ids))
        )[0]
        self.assertNotEqual(new_modcon.llista_preu.id, tarifa_social_id)
        self.assertEqual(new_modcon.data_inici, tommorrow)
        self.assertEqual(new_modcon.state, 'pendent')
        self.assertEqual(new_modcon.modcontractual_ant.id, modcon_ids[0])
