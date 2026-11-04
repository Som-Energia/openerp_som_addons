# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date, timedelta

from destral import testing


class TestModcontractual(testing.OOTestCaseWithCursor):

    def test_renovar_social_contract_creates_regular_pending_modcon(self):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        social_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social",
            "tarifa_20TD_SOM_INSULAR_SOCIAL",
        )[1]

        polissa_obj.send_signal(
            self.cursor, self.uid, [polissa_id], ["validar", "contracte"]
        )
        modcon_ids = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)]
        )
        year_ago = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        modcon_obj.write(self.cursor, self.uid, [modcon_ids[-1]], {
            "modcon_renovation_type": "automatic",
            "llista_preu": social_tariff_id,
            "data_final": tomorrow,
            "data_inici": year_ago,
        })

        regular_tariff_id = polissa_obj.mapping_tarifa_no_social(
            self.cursor, self.uid, polissa_id
        )

        modcon_obj.renovar(self.cursor, self.uid, [modcon_ids[-1]])

        modcon_ids_after = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)]
        )
        self.assertEqual(len(modcon_ids_after), len(modcon_ids) + 1)
        new_modcon_id = list(set(modcon_ids_after) - set(modcon_ids))[0]
        new_modcon = modcon_obj.browse(self.cursor, self.uid, new_modcon_id)
        self.assertEqual(new_modcon.llista_preu.id, regular_tariff_id)
        self.assertEqual(new_modcon.data_inici, tomorrow)
        self.assertEqual(new_modcon.state, "pendent")
        self.assertEqual(new_modcon.modcontractual_ant.id, modcon_ids[0])
        self.assertEqual(
            new_modcon.data_final,
            (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
        )

    def test_renovar_regular_contract_keeps_standard_renewal(self):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        regular_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada",
            "pricelist_periodes_20td_peninsula",
        )[1]
        polissa_obj.write(self.cursor, self.uid, polissa_id, {
            "llista_preu": regular_tariff_id,
        })
        polissa_obj.send_signal(
            self.cursor, self.uid, [polissa_id], ["validar", "contracte"]
        )
        modcon_ids = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)]
        )
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        modcon_obj.write(self.cursor, self.uid, [modcon_ids[0]], {
            "modcon_renovation_type": "automatic",
            "data_inici": (date.today() - timedelta(days=365)).strftime(
                "%Y-%m-%d"
            ),
            "data_final": tomorrow,
        })

        result = modcon_obj.renovar(self.cursor, self.uid, modcon_ids)

        self.assertTrue(result)
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)]
        ), modcon_ids)
        modcon = modcon_obj.browse(self.cursor, self.uid, modcon_ids[0])
        self.assertEqual(modcon.llista_preu.id, regular_tariff_id)
        self.assertTrue(modcon.data_final > tomorrow)

    def test_renovar_empty_selection(self):
        modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")

        self.assertTrue(modcon_obj.renovar(self.cursor, self.uid, []))
