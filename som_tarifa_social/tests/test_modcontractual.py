# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date, datetime, timedelta
import time

from destral import testing
import mock
from polissa_base import polissa_base
from som_polissa.exceptions import exceptions


class TestModcontractual(testing.OOTestCaseWithCursor):

    def test_renovar_social_contract_creates_regular_pending_modcon(self):
        self._assert_social_expiry(
            "atr", "tarifa_20TD_SOM_SOCIAL",
            "pricelist_periodes_20td_peninsula",
        )

    def _assert_social_expiry(self, billing_mode, social_reference,
                              regular_reference):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]
        social_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social",
            social_reference,
        )[1]
        regular_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", regular_reference,
        )[1]
        tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "tarifa_20TD",
        )[1]
        polissa_obj.write(self.cursor, self.uid, polissa_id, {
            "llista_preu": social_tariff_id,
            "mode_facturacio": billing_mode,
            "tarifa": tariff_id,
        })

        polissa_obj.send_signal(
            self.cursor, self.uid, [polissa_id], ["validar", "contracte"]
        )
        modcon_ids = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)]
        )
        self.assertEqual(len(modcon_ids), 1)
        current_id = modcon_ids[0]
        policy = polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(policy.modcontractual_activa.id, current_id)
        self.assertEqual(policy.llista_preu.id, social_tariff_id)
        self.assertEqual(policy.mode_facturacio, billing_mode)
        self.assertEqual(polissa_obj._get_tariff_zone_from_location(
            self.cursor, self.uid, policy.cups.id_municipi.id,
        ), "peninsula")
        year_ago = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        modcon_obj.write(self.cursor, self.uid, [current_id], {
            "modcon_renovation_type": "automatic",
            "llista_preu": social_tariff_id,
            "data_final": tomorrow,
            "data_inici": year_ago,
        })

        current = modcon_obj.browse(self.cursor, self.uid, current_id)
        self.assertEqual(current.llista_preu.id, social_tariff_id)
        self.assertEqual(current.mode_facturacio, billing_mode)
        self.assertEqual(current.state, "actiu")
        modcon_obj.renovar(self.cursor, self.uid, [current_id])

        modcon_ids_after = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)]
        )
        self.assertEqual(len(modcon_ids_after), len(modcon_ids) + 1)
        successor_ids = list(set(modcon_ids_after) - set(modcon_ids))
        self.assertEqual(len(successor_ids), 1)
        new_modcon_id = successor_ids[0]
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid,
            [("polissa_id", "=", polissa_id), ("state", "=", "pendent")],
        ), successor_ids)
        new_modcon = modcon_obj.browse(self.cursor, self.uid, new_modcon_id)
        self.assertEqual(new_modcon.llista_preu.id, regular_tariff_id)
        self.assertEqual(new_modcon.data_inici, tomorrow)
        self.assertEqual(new_modcon.state, "pendent")
        self.assertEqual(new_modcon.modcontractual_ant.id, current_id)
        self.assertEqual(new_modcon.mode_facturacio, billing_mode)
        self.assertEqual(
            new_modcon.data_final,
            (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
        )
        current = modcon_obj.browse(self.cursor, self.uid, current_id)
        self.assertEqual(current.modcontractual_seg.id, new_modcon_id)
        self.assertEqual(
            (datetime.strptime(current.data_final, "%Y-%m-%d")
             + timedelta(days=1)).strftime("%Y-%m-%d"),
            new_modcon.data_inici,
        )
        policy = polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(policy.modcontractual_activa.id, current_id)
        self.assertEqual(policy.llista_preu.id, social_tariff_id)
        self.assertEqual(current.state, "actiu")
        self.assertFalse(modcon_obj.cnd_activar_contracte(
            self.cursor, self.uid, [new_modcon_id],
        ))
        self.assertNotIn(new_modcon_id, modcon_obj.get_contractes_activar(
            self.cursor, self.uid, context={"delay_days": 0},
        ))

        due_date = datetime.strptime(tomorrow, "%Y-%m-%d")
        with mock.patch.object(polissa_base, "datetime", wraps=datetime) as clock:
            with mock.patch.object(polissa_base, "time", wraps=time) as day:
                clock.now.return_value = due_date
                day.strftime.return_value = tomorrow
                self.assertIn(new_modcon_id, modcon_obj.get_contractes_activar(
                    self.cursor, self.uid, context={"delay_days": 0},
                ))
                self.assertTrue(modcon_obj.cnd_activar_contracte(
                    self.cursor, self.uid, [new_modcon_id],
                ))
                # Run the cron's per-record activation steps in our transaction;
                # the cron itself opens and commits a separate cursor.
                if modcon_obj._check_pending_activation(
                        self.cursor, self.uid, new_modcon_id):
                    self.assertEqual(
                        modcon_obj._do_previous_actions_on_activation(
                            self.cursor, self.uid, new_modcon_id,
                        ), "OK",
                    )
                modcon_obj.write(
                    self.cursor, self.uid, [new_modcon_id], {"active": 1},
                    context={"sync": False},
                )
                modcon_obj.aplicar_modificacio(
                    self.cursor, self.uid, new_modcon_id,
                )

        policy = polissa_obj.browse(self.cursor, self.uid, polissa_id)
        successor = modcon_obj.browse(self.cursor, self.uid, new_modcon_id)
        self.assertEqual(policy.modcontractual_activa.id, new_modcon_id)
        self.assertEqual(policy.llista_preu.id, regular_tariff_id)
        self.assertEqual(policy.mode_facturacio, billing_mode)
        self.assertEqual(successor.state, "actiu")
        self.assertTrue(successor.active)
        self.assertEqual(successor.llista_preu.id, regular_tariff_id)
        self.assertNotEqual(
            modcon_obj.browse(self.cursor, self.uid, current_id).state, "actiu",
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

    def test_renovar_indexed_social_contract_activates_regular_modcon(self):
        self._assert_social_expiry(
            "index", "tarifa_indexada_20TD_peninsula_social",
            "pricelist_indexada_20td_peninsula_2024",
        )

    def test_renovar_invalid_target_rejected_before_policy_mutation(self):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018",
        )[1]
        social_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social", "tarifa_20TD_SOM_SOCIAL",
        )[1]
        tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "tarifa_20TD",
        )[1]
        polissa_obj.write(self.cursor, self.uid, polissa_id, {
            "llista_preu": social_tariff_id,
            "mode_facturacio": "atr",
            "tarifa": tariff_id,
        })
        polissa_obj.send_signal(
            self.cursor, self.uid, [polissa_id], ["validar", "contracte"],
        )
        domain = [("polissa_id", "=", polissa_id)]
        modcon_ids = modcon_obj.search(self.cursor, self.uid, domain)
        self.assertEqual(len(modcon_ids), 1)
        modcon_obj.write(self.cursor, self.uid, modcon_ids, {
            "modcon_renovation_type": "automatic",
            "data_inici": (date.today() - timedelta(days=365)).isoformat(),
            "data_final": (date.today() + timedelta(days=1)).isoformat(),
        })
        policy_fields = [
            "state", "llista_preu", "modcontractual_activa",
            "mode_facturacio", "tarifa",
        ]
        modcon_fields = [
            "state", "active", "llista_preu", "modcontractual_ant",
            "modcontractual_seg", "data_inici", "data_final",
            "mode_facturacio", "modcon_renovation_type",
        ]
        policy_before = polissa_obj.read(
            self.cursor, self.uid, polissa_id, policy_fields,
        )
        modcons_before = modcon_obj.read(
            self.cursor, self.uid, modcon_ids, modcon_fields,
        )
        self.assertEqual(policy_before["state"], "activa")
        self.assertEqual(policy_before["llista_preu"][0], social_tariff_id)
        self.assertEqual(modcons_before[0]["state"], "actiu")

        entered_states = []
        original_enter = polissa_obj.wkf_modcontractual

        def enter_modcon(cursor, uid, ids):
            result = original_enter(cursor, uid, ids)
            entered_states.append(polissa_obj.read(
                cursor, uid, polissa_id, policy_fields,
            ))
            return result

        for invalid_target in (0, False, None):
            # Only the resolver result is injected; workflow and writes remain real.
            with mock.patch.object(
                    polissa_obj, "mapping_tarifa_no_social",
                    return_value=invalid_target):
                with mock.patch.object(
                        polissa_obj, "wkf_modcontractual", new=enter_modcon):
                    with self.assertRaises(
                            exceptions.PolissaCannotChangeSocialTariff) as raised:
                        modcon_obj.renovar(self.cursor, self.uid, modcon_ids)

            expected_error = exceptions.PolissaCannotChangeSocialTariff(
                polissa_obj.browse(
                    self.cursor, self.uid, polissa_id,
                ).name, "to_regular",
            )
            self.assertEqual(raised.exception.to_dict(), expected_error.to_dict())

            # No caller rollback: rejection must precede mutation, not just undo it.
            self.assertEqual(
                modcon_obj.search(self.cursor, self.uid, domain), modcon_ids,
            )
            self.assertEqual(polissa_obj.read(
                self.cursor, self.uid, polissa_id, policy_fields,
            ), policy_before)
            self.assertEqual(modcon_obj.read(
                self.cursor, self.uid, modcon_ids, modcon_fields,
            ), modcons_before)
            self.assertEqual(
                entered_states, [],
                "Invalid renewal target mutated the policy: %r" % entered_states,
            )
