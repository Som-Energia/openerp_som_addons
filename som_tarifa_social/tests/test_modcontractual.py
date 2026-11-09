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
                              regular_reference, zone="peninsula",
                              expired_days=1):
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
            "mode_facturacio_generacio": billing_mode,
            "tarifa": tariff_id,
            "renovacio_auto": True,
        })

        polissa_obj.send_signal(
            self.cursor, self.uid, [polissa_id], ["validar", "contracte"]
        )
        modcon_ids = modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)]
        )
        self.assertEqual(len(modcon_ids), 1)
        current_id = modcon_ids[0]
        category_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social", "categ_tarifa_social",
        )[1]
        polissa_obj.write(self.cursor, self.uid, [polissa_id], {
            "category_id": [(4, category_id)],
        })
        categories_before = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["category_id"],
        )["category_id"]
        policy = polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(policy.modcontractual_activa.id, current_id)
        self.assertEqual(policy.llista_preu.id, social_tariff_id)
        self.assertEqual(policy.mode_facturacio, billing_mode)
        self.assertEqual(polissa_obj._get_tariff_zone_from_location(
            self.cursor, self.uid, policy.cups.id_municipi.id,
        ), zone)
        year_ago = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        modcon_obj.write(self.cursor, self.uid, [current_id], {
            "modcon_renovation_type": "automatic",
            "llista_preu": social_tariff_id,
            "data_final": (
                date.today() - timedelta(days=expired_days)
            ).isoformat(),
            "data_inici": year_ago,
        })

        current = modcon_obj.browse(self.cursor, self.uid, current_id)
        self.assertEqual(current.llista_preu.id, social_tariff_id)
        self.assertEqual(current.mode_facturacio, billing_mode)
        self.assertEqual(current.state, "actiu")
        self.assertIn(current_id, modcon_obj.get_contractes_renovar(
            self.cursor, self.uid, context={"delay_days": -1},
        ))
        modcon_obj.renovar(
            self.cursor, self.uid, [current_id], context={"sync": False},
        )

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
        self.assertEqual(new_modcon.mode_facturacio_generacio, billing_mode)
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
        self.assertEqual(polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["category_id"],
        )["category_id"], categories_before)
        # A retry must neither duplicate the pending change nor renew its dates.
        pending_before = modcon_obj.read(
            self.cursor, self.uid, new_modcon_id,
            ["data_inici", "data_final", "state"],
        )
        modcon_obj.renovar(self.cursor, self.uid, [current_id, new_modcon_id])
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid, [("polissa_id", "=", polissa_id)],
        ), modcon_ids_after)
        self.assertEqual(modcon_obj.read(
            self.cursor, self.uid, new_modcon_id,
            ["data_inici", "data_final", "state"],
        ), pending_before)
        self.assertNotIn(current_id, modcon_obj.get_contractes_renovar(
            self.cursor, self.uid, context={"delay_days": -1},
        ))
        self._assert_invoice_price_versions(
            polissa_id, social_tariff_id, regular_tariff_id, tomorrow,
        )
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
        self.assertEqual(policy.mode_facturacio_generacio, billing_mode)
        categories_after = polissa_obj.read(
            self.cursor, self.uid, polissa_id, ["category_id"],
        )["category_id"]
        self.assertNotIn(category_id, categories_after)
        self.assertEqual(set(categories_after),
                         set(categories_before) - {category_id})
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

    def test_renovar_wizard_warning_restores_policy_without_caller_rollback(self):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        wizard_obj = self.openerp.pool.get("giscedata.polissa.crear.contracte")
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018",
        )[1]
        social_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social", "tarifa_20TD_SOM_SOCIAL",
        )[1]
        regular_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada",
            "pricelist_periodes_20td_peninsula",
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
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        modcon_obj.write(self.cursor, self.uid, modcon_ids, {
            "modcon_renovation_type": "automatic",
            "data_inici": (date.today() - timedelta(days=365)).isoformat(),
            "data_final": tomorrow,
        })
        policy_fields = [
            "state", "llista_preu", "modcontractual_activa",
            "mode_facturacio", "tarifa", "data_alta", "data_baixa",
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
        self.assertEqual(policy_before["modcontractual_activa"][0], modcon_ids[0])
        self.assertEqual(modcons_before[0]["state"], "actiu")
        self.assertEqual(modcons_before[0]["llista_preu"][0], social_tariff_id)
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid, domain + [("state", "=", "pendent")],
        ), [])

        warning_marker = "controlled-social-renewal-warning"
        onchange_states = []
        original_onchange = wizard_obj.onchange_duracio

        def warning_onchange(cursor, uid, ids, data_inici, duracio, context=None):
            result = original_onchange(
                cursor, uid, ids, data_inici, duracio, context=context,
            )
            self.assertEqual(context["active_id"], polissa_id)
            self.assertEqual(data_inici, tomorrow)
            self.assertEqual(duracio, "nou")
            onchange_states.append(polissa_obj.read(
                cursor, uid, polissa_id, policy_fields,
            ))
            result["warning"] = {
                "title": "Controlled renewal warning", "message": warning_marker,
            }
            return result

        # Inject only the warning; pricing writes, workflow and undo stay real.
        with mock.patch.object(
                wizard_obj, "onchange_duracio", new=warning_onchange):
            with self.assertRaises(exceptions.UnexpectedException) as raised:
                modcon_obj.renovar(self.cursor, self.uid, modcon_ids)

        self.assertEqual(raised.exception.code, "Unexpected")
        self.assertIn(warning_marker, raised.exception.to_dict()["error"])
        self.assertEqual(len(onchange_states), 1)
        self.assertEqual(onchange_states[0]["state"], "modcontractual")
        self.assertEqual(onchange_states[0]["llista_preu"][0], regular_tariff_id)
        # No savepoint or caller rollback: observe the method-local undo result.
        self.assertEqual(polissa_obj.read(
            self.cursor, self.uid, polissa_id, policy_fields,
        ), policy_before)
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid, domain,
        ), modcon_ids)
        self.assertEqual(modcon_obj.read(
            self.cursor, self.uid, modcon_ids, modcon_fields,
        ), modcons_before)
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid, domain + [("state", "=", "pendent")],
        ), [])

    def test_renovar_post_creation_failure_requires_caller_rollback(self):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        modcon_obj = self.openerp.pool.get("giscedata.polissa.modcontractual")
        wizard_obj = self.openerp.pool.get("giscedata.polissa.crear.contracte")
        imd_obj = self.openerp.pool.get("ir.model.data")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018",
        )[1]
        social_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_tarifa_social", "tarifa_20TD_SOM_SOCIAL",
        )[1]
        regular_tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada",
            "pricelist_periodes_20td_peninsula",
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
        current_id = modcon_ids[0]
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        modcon_obj.write(self.cursor, self.uid, modcon_ids, {
            "modcon_renovation_type": "automatic",
            "data_inici": (date.today() - timedelta(days=365)).isoformat(),
            "data_final": tomorrow,
        })
        policy_fields = [
            "state", "llista_preu", "modcontractual_activa", "mode_facturacio",
            "tarifa", "data_alta", "data_baixa", "renovacio_auto",
            "data_firma_contracte",
        ]
        modcon_fields = [
            "state", "active", "llista_preu", "modcontractual_ant",
            "modcontractual_seg", "data_inici", "data_final",
            "mode_facturacio", "modcon_renovation_type", "data_firma_contracte",
        ]
        policy_before = polissa_obj.read(
            self.cursor, self.uid, polissa_id, policy_fields,
        )
        modcons_before = modcon_obj.read(
            self.cursor, self.uid, modcon_ids, modcon_fields,
        )
        self.assertEqual(policy_before["state"], "activa")
        self.assertEqual(policy_before["llista_preu"][0], social_tariff_id)
        self.assertEqual(policy_before["modcontractual_activa"][0], current_id)
        self.assertEqual(modcons_before[0]["state"], "actiu")
        self.assertEqual(modcons_before[0]["llista_preu"][0], social_tariff_id)
        self.assertFalse(modcons_before[0]["modcontractual_seg"])

        fault_marker = "controlled-social-renewal-post-creation-failure"
        creation_states = []
        remaining_ids = []
        original_create = wizard_obj.action_crear_contracte

        def fail_after_creation(cursor, uid, ids, context=None):
            policy_entered = polissa_obj.read(
                cursor, uid, polissa_id, policy_fields,
            )
            original_create(cursor, uid, ids, context=context)
            created_ids = modcon_obj.search(cursor, uid, domain)
            creation_states.append({
                "entered": policy_entered,
                "policy": polissa_obj.read(
                    cursor, uid, polissa_id, policy_fields,
                ),
                "modcons": modcon_obj.read(
                    cursor, uid, created_ids, modcon_fields,
                ),
            })
            raise RuntimeError(fault_marker)

        # Simulate the RPC caller's exception boundary without committing fixtures.
        # The domain exception reaches this handler BEFORE assertRaises catches it.
        with mock.patch.object(
                wizard_obj, "action_crear_contracte", new=fail_after_creation):
            with self.assertRaises(exceptions.UnexpectedException) as raised:
                self.cursor.savepoint("social_renewal_caller")
                try:
                    modcon_obj.renovar(self.cursor, self.uid, modcon_ids)
                except exceptions.UnexpectedException:
                    # Observe method-local undo, before the caller rolls back SQL.
                    remaining_ids.extend(modcon_obj.search(
                        self.cursor, self.uid, domain,
                    ))
                    self.cursor.rollback(savepoint="social_renewal_caller")
                    raise
                finally:
                    self.cursor.release("social_renewal_caller")

        self.assertEqual(raised.exception.code, "Unexpected")
        self.assertIn(fault_marker, raised.exception.to_dict()["error"])
        self.assertEqual(len(creation_states), 1)
        partial = creation_states[0]
        self.assertEqual(partial["entered"]["state"], "modcontractual")
        self.assertEqual(partial["entered"]["llista_preu"][0], regular_tariff_id)
        self.assertEqual(partial["policy"]["modcontractual_activa"][0], current_id)
        self.assertEqual(len(partial["modcons"]), 2)
        successors = [
            modcon for modcon in partial["modcons"] if modcon["id"] != current_id
        ]
        self.assertEqual(len(successors), 1)
        successor = successors[0]
        self.assertEqual(successor["state"], "pendent")
        self.assertEqual(successor["llista_preu"][0], regular_tariff_id)
        self.assertEqual(successor["modcontractual_ant"][0], current_id)
        self.assertEqual(successor["data_inici"], tomorrow)
        self.assertEqual(successor["data_final"],
                         (date.today() + timedelta(days=365)).isoformat())
        predecessor = [
            modcon for modcon in partial["modcons"] if modcon["id"] == current_id
        ][0]
        self.assertEqual(predecessor["modcontractual_seg"][0], successor["id"])
        self.assertEqual(predecessor["data_final"], date.today().isoformat())
        self.assertNotEqual(predecessor, modcons_before[0])
        # Undo is not SQL atomicity: the genuine successor survives until rollback.
        self.assertEqual(set(remaining_ids), set(modcon_ids + [successor["id"]]))

        # Fresh ORM reads, not previously browsed records or fixture teardown.
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid, domain,
        ), modcon_ids)
        self.assertEqual(modcon_obj.search(
            self.cursor, self.uid, [("id", "=", successor["id"])],
            context={"active_test": False},
        ), [])
        self.assertEqual(polissa_obj.read(
            self.cursor, self.uid, polissa_id, policy_fields,
        ), policy_before)
        self.assertEqual(modcon_obj.read(
            self.cursor, self.uid, modcon_ids, modcon_fields,
        ), modcons_before)

    def _assert_invoice_price_versions(self, polissa_id, social_tariff_id,
                                       regular_tariff_id, activation_date):
        """Use the invoice engine's price selection across the pending change."""
        version_obj = self.openerp.pool.get("product.pricelist.version")
        invoice_start = (date.today() - timedelta(days=7)).isoformat()
        invoice_end = (date.today() + timedelta(days=7)).isoformat()
        # Isolate price selection from demo price rules and their dependencies.
        existing = version_obj.search(self.cursor, self.uid, [
            ("pricelist_id", "in", [social_tariff_id, regular_tariff_id]),
        ], context={"active_test": False})
        version_obj.unlink(self.cursor, self.uid, existing)
        for pricelist_id in (social_tariff_id, regular_tariff_id):
            version_obj.create(self.cursor, self.uid, {
                "name": "Social expiry test prices",
                "pricelist_id": pricelist_id,
                "date_start": invoice_start,
                "date_end": invoice_end,
            })
        self.openerp.pool.get("res.config").set(
            self.cursor, self.uid, "auto_giscedata_pricelist_change_enabled", "1",
        )
        versions = self.openerp.pool.get(
            "giscedata.facturacio.facturador"
        ).versions_de_preus_ids(
            self.cursor, self.uid, polissa_id, invoice_start, invoice_end,
        )
        self.assertEqual(version_obj.browse(
            self.cursor, self.uid, versions[invoice_start],
        ).pricelist_id.id, social_tariff_id)
        self.assertEqual(version_obj.browse(
            self.cursor, self.uid, versions[activation_date],
        ).pricelist_id.id, regular_tariff_id)

    def test_renovar_delayed_social_expiry_keeps_contiguous_dates(self):
        self._assert_social_expiry(
            "atr", "tarifa_20TD_SOM_SOCIAL",
            "pricelist_periodes_20td_peninsula", expired_days=7,
        )

    def _assert_insular_social_expiry(self, zone, billing_mode):
        polissa_obj = self.openerp.pool.get("giscedata.polissa")
        if billing_mode == "atr":
            social_reference = "tarifa_20TD_SOM_INSULAR_SOCIAL"
            regular_reference = "pricelist_periodes_20td_insular"
        else:
            social_reference = "tarifa_indexada_20TD_{}_social".format(zone)
            regular_reference = "pricelist_indexada_20td_{}_2024".format(zone)
        with mock.patch.object(
                polissa_obj, "_get_tariff_zone_from_location", return_value=zone):
            self._assert_social_expiry(
                billing_mode, social_reference, regular_reference, zone=zone,
            )

    def test_renovar_period_social_expiry_in_balears(self):
        self._assert_insular_social_expiry("balears", "atr")

    def test_renovar_period_social_expiry_in_canaries(self):
        self._assert_insular_social_expiry("canaries", "atr")

    def test_renovar_indexed_social_expiry_in_balears(self):
        self._assert_insular_social_expiry("balears", "index")

    def test_renovar_indexed_social_expiry_in_canaries(self):
        self._assert_insular_social_expiry("canaries", "index")
