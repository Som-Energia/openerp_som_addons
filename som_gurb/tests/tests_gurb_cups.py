# -*- coding: utf-8 -*-
from __future__ import absolute_import

import mock
from .tests_gurb_base import TestsGurbBase
from osv import osv
from datetime import datetime, timedelta


class TestsGurbCups(TestsGurbBase):

    def _assert_account_code(self, many2one_value, expected_code):
        self.assertEqual(many2one_value[1].split(' ', 1)[0], expected_code)

    def _assert_partner_receivable_account(self, partner_id, many2one_value):
        partner_o = self.openerp.pool.get("res.partner")
        partner = partner_o.read(
            self.cursor, self.uid, partner_id, ["property_account_receivable"]
        )
        self.assertEqual(
            many2one_value[0], partner["property_account_receivable"][0]
        )

    def test_gurb_cups_percentage(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        gurb_cups_beta_o = self.openerp.pool.get("som.gurb.cups.beta")

        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]

        gurb_beta_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_beta_0001"
        )[1]
        gurb_beta_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_beta_0002"
        )[1]

        gurb_cups_beta_o.write(self.cursor, self.uid, gurb_beta_id_1, {"gift_beta_kw": 0.5})
        gurb_cups_beta_o.write(self.cursor, self.uid, gurb_beta_id_2, {"gift_beta_kw": 0.5})

        percentatge_1 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_1, ['beta_percentage']
        )['beta_percentage']
        percentatge_2 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_2, ['beta_percentage']
        )['beta_percentage']

        self.assertEqual(percentatge_1, 40.0)
        self.assertEqual(percentatge_2, 40.0)

    def test_gurb_is_owner(self):

        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")

        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]
        owner_cups_1 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_1, ["owner_cups"]
        )["owner_cups"]
        owner_cups_2 = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id_2, ["owner_cups"]
        )["owner_cups"]

        self.assertEqual(owner_cups_1, True)
        self.assertEqual(owner_cups_2, False)

    def test_wizard_gurb_create_new_beta(self):
        context = {}

        gurb_cups_beta_o = self.openerp.pool.get("som.gurb.cups.beta")

        gurb_cups_id = self.get_references()['gurb_cups_id']
        start_date = "2015-02-01"
        new_beta_kw = 1.5
        new_extra_beta_kw = 0.5
        new_gift_beta = 1

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw,
                new_gift_beta, context=context
            )

        new_beta_kw = -10

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw,
                new_gift_beta, context=context
            )

        new_beta_kw = 0
        new_extra_beta_kw = 0
        new_gift_beta = 0

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw,
                new_gift_beta, context=context
            )

        start_date = (datetime.today() + timedelta(days=20)).strftime("%Y-%m-%d")
        new_beta_kw = 1.5
        new_extra_beta_kw = 0.5
        new_gift_beta = 1

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw,
                new_gift_beta, context=context
            )

        new_beta_kw = 2.5
        new_extra_beta_kw = 1
        new_gift_beta = 0
        start_date = "2017-02-01"

        with self.assertRaises(osv.except_osv):
            self.create_new_gurb_cups_beta(
                gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw,
                new_gift_beta, context=context
            )

        new_beta_kw = 3
        new_extra_beta_kw = 2
        new_gift_beta = 1
        start_date = (datetime.today()).strftime("%Y-%m-%d")

        context["activate"] = False

        self.create_new_gurb_cups_beta(
            gurb_cups_id, start_date, new_beta_kw, new_extra_beta_kw, new_gift_beta, context=context
        )
        gurb_cups_beta_id = gurb_cups_beta_o.search(
            self.cursor, self.uid, [("gurb_cups_id", "=", gurb_cups_id), ("future_beta", "=", True)]
        )
        self.assertEqual(len(gurb_cups_beta_id), 1)

    def test_gurb_cups_activation(self):
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        gurb_cups_beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        pol_o = self.openerp.pool.get("giscedata.polissa")

        gurb_cups_id = self.get_references()["gurb_cups_id"]
        gurb_cups_beta_id = self.get_references()["gurb_cups_beta_2_id"]

        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id, {"start_date": False})
        gurb_cups_beta_o.write(self.cursor, self.uid, gurb_cups_beta_id, {"future_beta": True})
        gurb_cups_o.send_signal(self.cursor, self.uid, [gurb_cups_id], "button_create_cups")
        gurb_cups_o.activate_or_modify_gurb_cups(self.cursor, self.uid, gurb_cups_id, "2024-01-01")

        pol_id = gurb_cups_o.read(
            self.cursor, self.uid, gurb_cups_id, ["polissa_id"]
        )["polissa_id"][0]

        pol_br = pol_o.browse(self.cursor, self.uid, pol_id)
        gurb_cups_br = gurb_cups_o.browse(self.cursor, self.uid, gurb_cups_id)
        gurb_cups_beta_br = gurb_cups_beta_o.browse(self.cursor, self.uid, gurb_cups_id)

        self.assertEqual(len(pol_br.serveis), 1)
        self.assertEqual(pol_br.serveis[0].polissa_id.id, pol_id)
        self.assertEqual(gurb_cups_br.start_date, "2024-01-01")
        self.assertEqual(gurb_cups_br.state, "active")
        self.assertEqual(gurb_cups_beta_br.future_beta, False)

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.create_initial_invoice")
    def test_create_initial_invoices_collects_exception(self, mock_create_invoice):
        mock_create_invoice.side_effect = [ValueError("Invoice failed"), (42, False)]
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        refs = self.get_references()
        gurb_cups_id = refs["gurb_cups_id"]

        invoice_ids, errors = gurb_cups_o.create_initial_invoices(
            self.cursor, self.uid, [gurb_cups_id, refs["owner_gurb_cups_id"]]
        )

        self.assertEqual(invoice_ids, [42])
        self.assertEqual(errors, [
            "[GURB CUPS ID {}]: Invoice failed".format(gurb_cups_id)
        ])

    def test_cancel_gurb_cups_preserves_beta_history(self):
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        refs = self.get_references()
        gurb_cups_id = refs["gurb_cups_id"]
        historical_beta_id = refs["gurb_cups_beta_2_id"]
        beta_o.write(self.cursor, self.uid, historical_beta_id, {
            "active": False,
            "end_date": "2016-01-31",
        })
        active_beta_id = beta_o.create(self.cursor, self.uid, {
            "gurb_cups_id": gurb_cups_id,
            "active": True,
            "start_date": "2016-02-01",
            "beta_kw": 3,
            "extra_beta_kw": 0,
            "gift_beta_kw": 0,
        })
        gurb_cups_o.send_signal(self.cursor, self.uid, [gurb_cups_id], [
            "button_create_cups", "button_activate_cups",
            "button_coming_cancellation",
        ])

        gurb_cups_o.cancel_gurb_cups(
            self.cursor, self.uid, gurb_cups_id, "2016-06-06",
            context={"active_test": False}
        )

        active_beta = beta_o.browse(self.cursor, self.uid, active_beta_id)
        self.assertFalse(active_beta.active)
        self.assertEqual(active_beta.end_date, "2016-06-06")
        historical_beta = beta_o.browse(
            self.cursor, self.uid, historical_beta_id
        )
        self.assertFalse(historical_beta.active)
        self.assertEqual(historical_beta.end_date, "2016-01-31")
        unrelated_beta = beta_o.browse(
            self.cursor, self.uid, refs["gurb_cups_beta_id"]
        )
        self.assertTrue(unrelated_beta.active)
        self.assertFalse(unrelated_beta.end_date)

    def _prepare_confirmed_cancellation(self, pending_signal=None):
        cups_o = self.openerp.pool.get("som.gurb.cups")
        beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        product_o = self.openerp.pool.get("product.product")
        refs = self.get_references()
        self.activar_polissa_CUPS()
        cups_o.send_signal(self.cursor, self.uid, [refs["gurb_cups_id"]], [
            "button_create_cups", "button_activate_cups",
        ])
        if pending_signal:
            cups_o.send_signal(
                self.cursor, self.uid, [refs["gurb_cups_id"]], pending_signal
            )
        cups_o.add_service_to_contract(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-02-01"
        )
        service_ids = service_o.search(
            self.cursor, self.uid, [("polissa_id", "=", refs["pol_id"])]
        )
        self.assertEqual(len(service_ids), 1)
        refs["service_id"] = service_ids[0]
        other_product_id = product_o.copy(
            self.cursor, self.uid, refs["product_id"], {"name": "Unrelated service"}
        )
        refs["unrelated_service_id"] = service_o.copy(
            self.cursor, self.uid, service_ids[0], {"producte": other_product_id}
        )
        refs["closed_service_id"] = service_o.copy(
            self.cursor, self.uid, service_ids[0], {"data_fi": "2016-03-01"}
        )
        beta_o.write(self.cursor, self.uid, refs["gurb_cups_beta_2_id"], {
            "active": False, "end_date": "2016-01-31",
        })
        refs["active_beta_id"] = beta_o.create(self.cursor, self.uid, {
            "gurb_cups_id": refs["gurb_cups_id"],
            "active": True,
            "start_date": "2016-02-01",
            "beta_kw": 3,
            "extra_beta_kw": 0,
            "gift_beta_kw": 0,
        })
        return refs

    def _assert_confirmed_cancellation(self, refs, end_date="2016-06-06"):
        cups_o = self.openerp.pool.get("som.gurb.cups")
        beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        cups = cups_o.browse(
            self.cursor, self.uid, refs["gurb_cups_id"], context={"active_test": False}
        )
        self.assertEqual(cups.state, "cancel")
        self.assertFalse(cups.active)
        self.assertEqual(cups.end_date, end_date)
        beta = beta_o.browse(self.cursor, self.uid, refs["active_beta_id"])
        self.assertFalse(beta.active)
        self.assertEqual(beta.end_date, end_date)
        historical_beta = beta_o.browse(
            self.cursor, self.uid, refs["gurb_cups_beta_2_id"]
        )
        self.assertEqual(historical_beta.end_date, "2016-01-31")
        unrelated_beta = beta_o.browse(self.cursor, self.uid, refs["gurb_cups_beta_id"])
        self.assertTrue(unrelated_beta.active)
        self.assertFalse(unrelated_beta.end_date)
        self.assertEqual(service_o.read(
            self.cursor, self.uid, refs["service_id"], ["data_fi"]
        )["data_fi"], end_date)
        self.assertFalse(service_o.read(
            self.cursor, self.uid, refs["unrelated_service_id"], ["data_fi"]
        )["data_fi"])
        self.assertEqual(service_o.read(
            self.cursor, self.uid, refs["closed_service_id"], ["data_fi"]
        )["data_fi"], "2016-03-01")

    def test_confirmed_cancellation_from_active(self):
        refs = self._prepare_confirmed_cancellation()
        cups_o = self.openerp.pool.get("som.gurb.cups")
        context = {
            "active_ids": [refs["unrelated_service_id"]],
            "gurb_cancellation_confirmed": True,
        }
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06",
            context=context
        )
        self._assert_confirmed_cancellation(refs)
        self.assertEqual(context, {
            "active_ids": [refs["unrelated_service_id"]],
            "gurb_cancellation_confirmed": True,
        })

    def test_confirmed_cancellation_from_pending_modification_keeps_beta_unpromoted(self):
        refs = self._prepare_confirmed_cancellation()
        cups_o = self.openerp.pool.get("som.gurb.cups")
        beta_o = self.openerp.pool.get("som.gurb.cups.beta")
        self.create_new_gurb_cups_beta(
            refs["gurb_cups_id"], "2016-04-01", 1.5, 0.5, 0,
            context={"activate": False}
        )
        pending_ids = beta_o.search(self.cursor, self.uid, [
            ("gurb_cups_id", "=", refs["gurb_cups_id"]),
            ("future_beta", "=", True),
            ("active", "=", True),
        ])
        self.assertEqual(len(pending_ids), 1)
        self.assertEqual(cups_o.read(
            self.cursor, self.uid, refs["gurb_cups_id"], ["state"]
        )["state"], "comming_modification")
        beta_fields = ["start_date", "beta_kw", "extra_beta_kw", "gift_beta_kw", "future_beta"]
        pending_before = beta_o.read(self.cursor, self.uid, pending_ids[0], beta_fields)
        current_before = beta_o.read(
            self.cursor, self.uid, refs["active_beta_id"], beta_fields
        )
        self.assertTrue(pending_before["future_beta"])
        self.assertFalse(current_before["future_beta"])
        self.assertLessEqual(pending_before["start_date"], "2016-06-06")
        context = {"gurb_cancellation_confirmed": True, "active_test": False}
        original_context = context.copy()

        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06", context=context
        )

        self._assert_confirmed_cancellation(refs)
        pending = beta_o.browse(self.cursor, self.uid, pending_ids[0])
        self.assertFalse(pending.active)
        self.assertEqual(pending.end_date, "2016-06-06")
        self.assertEqual(
            beta_o.read(self.cursor, self.uid, pending_ids[0], beta_fields), pending_before
        )
        self.assertEqual(beta_o.read(
            self.cursor, self.uid, refs["active_beta_id"], beta_fields
        ), current_before)
        self.assertEqual(context, original_context)

    def test_cancel_gurb_cups_preserves_original_signature(self):
        import inspect
        from som_gurb.models.som_gurb_cups import SomGurbCups

        getargspec = getattr(inspect, "getfullargspec", None) or inspect.getargspec
        argspec = getargspec(SomGurbCups.cancel_gurb_cups)
        self.assertEqual(argspec.args, [
            "self", "cursor", "uid", "gurb_cups_id", "end_date", "context",
        ])
        self.assertEqual(argspec.defaults, (None,))
        self.assertIsNone(argspec.varargs)
        self.assertIsNone(getattr(argspec, "varkw", getattr(argspec, "keywords", None)))

    def test_confirmed_cancellation_with_positional_context(self):
        refs = self._prepare_confirmed_cancellation()
        context = {"gurb_cancellation_confirmed": True, "active_test": False}
        self.openerp.pool.get("som.gurb.cups").cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06", context
        )
        self._assert_confirmed_cancellation(refs)
        self.assertEqual(context, {
            "gurb_cancellation_confirmed": True, "active_test": False,
        })

    def test_unconfirmed_cancellation_with_positional_context(self):
        refs = self._prepare_confirmed_cancellation()
        context = {"gurb_cancellation_confirmed": False, "active_test": False}
        cups_o = self.openerp.pool.get("som.gurb.cups")
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06", context
        )
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        self.assertEqual(cups.state, "atr_pending")
        self.assertTrue(cups.active)
        self.assertFalse(cups.end_date)
        beta = self.openerp.pool.get("som.gurb.cups.beta").browse(
            self.cursor, self.uid, refs["active_beta_id"]
        )
        self.assertTrue(beta.active)
        self.assertFalse(beta.end_date)
        self.assertFalse(self.openerp.pool.get("giscedata.facturacio.services").read(
            self.cursor, self.uid, refs["service_id"], ["data_fi"]
        )["data_fi"])
        self.assertEqual(context, {
            "gurb_cancellation_confirmed": False, "active_test": False,
        })

    def test_confirmed_cancellation_from_atr_pending(self):
        refs = self._prepare_confirmed_cancellation("button_atr_pending")
        self.openerp.pool.get("som.gurb.cups").cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06",
            context={"gurb_cancellation_confirmed": True}
        )
        self._assert_confirmed_cancellation(refs)

    def test_confirmed_cancellation_from_comming_cancellation(self):
        refs = self._prepare_confirmed_cancellation("button_coming_cancellation")
        self.openerp.pool.get("som.gurb.cups").cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06",
            context={"gurb_cancellation_confirmed": True}
        )
        self._assert_confirmed_cancellation(refs)

    def test_confirmed_cancellation_is_idempotent(self):
        refs = self._prepare_confirmed_cancellation("button_coming_cancellation")
        cups_o = self.openerp.pool.get("som.gurb.cups")
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06",
            context={"gurb_cancellation_confirmed": True}
        )
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-07-01",
            context={"active_test": False, "gurb_cancellation_confirmed": True}
        )
        self._assert_confirmed_cancellation(refs)

    def test_confirmed_cancellation_rejects_unsupported_state(self):
        cups_o = self.openerp.pool.get("som.gurb.cups")
        refs = self.get_references()
        with self.assertRaises(osv.except_osv):
            cups_o.cancel_gurb_cups(
                self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06",
                context={"gurb_cancellation_confirmed": True}
            )
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        self.assertEqual(cups.state, "draft")
        self.assertTrue(cups.active)
        self.assertFalse(cups.end_date)

    def test_confirmed_cancellation_scopes_services_despite_caller_selection(self):
        refs = self._prepare_confirmed_cancellation()
        cups_o = self.openerp.pool.get("som.gurb.cups")
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        second_service_id = service_o.copy(
            self.cursor, self.uid, refs["service_id"],
            {"producte": refs["owner_product_id"]}
        )
        other_contract_service_id = service_o.copy(
            self.cursor, self.uid, refs["service_id"],
            {"polissa_id": refs["owner_pol_id"]}
        )
        context = {
            "active_id": refs["unrelated_service_id"],
            "active_ids": [refs["unrelated_service_id"]],
            "dont_raise_exception": False,
            "gurb_cancellation_confirmed": True,
        }
        original_context = context.copy()
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06",
            context=context
        )
        self._assert_confirmed_cancellation(refs)
        self.assertEqual(service_o.read(
            self.cursor, self.uid, second_service_id, ["data_fi"]
        )["data_fi"], "2016-06-06")
        self.assertFalse(service_o.read(
            self.cursor, self.uid, other_contract_service_id, ["data_fi"]
        )["data_fi"])
        self.assertEqual(context, original_context)

    def test_confirmed_cancellation_without_open_service(self):
        refs = self._prepare_confirmed_cancellation()
        service_o = self.openerp.pool.get("giscedata.facturacio.services")
        service_o.write(
            self.cursor, self.uid, refs["service_id"], {"data_fi": "2016-04-01"}
        )
        cups_o = self.openerp.pool.get("som.gurb.cups")
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06",
            context={"gurb_cancellation_confirmed": True}
        )
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        self.assertEqual(cups.state, "cancel")
        self.assertFalse(cups.active)
        self.assertEqual(service_o.read(
            self.cursor, self.uid, refs["service_id"], ["data_fi"]
        )["data_fi"], "2016-04-01")

    def test_unconfirmed_cancellation_from_active_preserves_service(self):
        refs = self._prepare_confirmed_cancellation()
        cups_o = self.openerp.pool.get("som.gurb.cups")
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06"
        )
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        self.assertEqual(cups.state, "atr_pending")
        self.assertTrue(cups.active)
        self.assertFalse(cups.end_date)
        beta = self.openerp.pool.get("som.gurb.cups.beta").browse(
            self.cursor, self.uid, refs["active_beta_id"]
        )
        self.assertTrue(beta.active)
        self.assertFalse(beta.end_date)
        self.assertFalse(self.openerp.pool.get("giscedata.facturacio.services").read(
            self.cursor, self.uid, refs["service_id"], ["data_fi"]
        )["data_fi"])

    def test_unconfirmed_cancellation_from_atr_pending_keeps_legacy_state(self):
        refs = self._prepare_confirmed_cancellation("button_atr_pending")
        cups_o = self.openerp.pool.get("som.gurb.cups")
        cups_o.cancel_gurb_cups(
            self.cursor, self.uid, refs["gurb_cups_id"], "2016-06-06"
        )
        cups = cups_o.browse(self.cursor, self.uid, refs["gurb_cups_id"])
        # Legacy M2 handling closes data without a valid workflow transition.
        self.assertEqual(cups.state, "atr_pending")
        self.assertFalse(cups.active)
        self.assertEqual(cups.end_date, "2016-06-06")
        beta = self.openerp.pool.get("som.gurb.cups.beta").browse(
            self.cursor, self.uid, refs["active_beta_id"]
        )
        self.assertFalse(beta.active)
        self.assertEqual(beta.end_date, "2016-06-06")
        self.assertEqual(self.openerp.pool.get("giscedata.facturacio.services").read(
            self.cursor, self.uid, refs["service_id"], ["data_fi"]
        )["data_fi"], "2016-06-06")

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.generate_gurb_invoice_base64")
    def test_create_initial__invoice_bank_transfer(
        self, generate_gurb_invoice_base64_mock_function
    ):
        generate_gurb_invoice_base64_mock_function.return_value = (
            "JVBERi0xLjAKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUj4+"
            "ZW5kb2JqCjIgMCBvYmo8PC9UeXBlL1BhZ2VzL0tpZHNbMyAwIFJdL0NvdW50"
            "IDE+PmVuZG9iagozIDAgb2JqPDwvVHlwZS9QYWdlL1BhcmVudCAyIDAgUi9S"
            "ZXNvdXJjZXM8PD4+L01lZGlhQm94WzAgMCA5IDldPj5lbmRvYmoKeHJlZgow"
            "IDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAw"
            "MDAwMDAwNTIgMDAwMDAgbiAKMDAwMDAwMDEwMSAwMDAwMCBuIAp0cmFpbGVy"
            "PDwvUm9vdCAxIDAgUi9TaXplIDQ+PgpzdGFydHhyZWYKMTc0CiUlRU9G"
        )
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        invoice_o = self.openerp.pool.get("account.invoice")
        line_o = self.openerp.pool.get("account.invoice.line")
        self.maxDiff = None
        gurb_cups_id = self.get_references()["gurb_cups_id"]
        ctx = {"tpv": False}

        invoice_id, errs = gurb_cups_o.create_initial_invoice(
            self.cursor, self.uid, gurb_cups_id, context=ctx)

        self.assertFalse(errs)
        self.assertTrue(invoice_id)
        inv = invoice_o.read(self.cursor, self.uid, invoice_id)
        self._assert_partner_receivable_account(inv['partner_id'][0], inv['account_id'])
        self.assertEqual(inv['partner_id'][1], 'GISCE')
        self.assertEqual(inv['origin'], 'GURBCUPSID2')
        self.assertEqual(inv['reference'], 'GURBCUPSID2')
        self.assertEqual(inv['date_invoice'], datetime.today().strftime('%Y-%m-%d'))
        self.assertEqual(inv['amount_untaxed'], 3.75)
        self.assertEqual(inv['amount_tax'], 0.79)
        self.assertEqual(inv['amount_total'], 4.54)
        self.assertEqual(inv['type'], 'out_invoice')
        self.assertEqual(inv['state'], 'draft')
        self.assertEqual(len(inv['invoice_line']), 1)
        self.assertEqual(len(inv['tax_line']), 1)
        self.assertEqual(inv["residual"], 4.54)
        self.assertEqual(inv["saldo"], 4.54)
        self.assertEqual(inv['journal_id'][1], u'Factures GURB')
        self.assertEqual(inv['payment_type'][1], u'Recibo domiciliado')
        line = line_o.read(self.cursor, self.uid, inv['invoice_line'][0])
        self.assertEqual(line['name'], u"Cost d'adhesió GURB GRUP 001")
        self.assertEqual(line['quantity'], 1.0)
        self.assertEqual(line['price_unit'], 3.75)
        self._assert_account_code(line['account_id'], '705000000104')

    @mock.patch("som_gurb.models.som_gurb_cups.SomGurbCups.generate_gurb_invoice_base64")
    def test_create_initial_invoice__invoice_tpv_payment(
        self, generate_gurb_invoice_base64_mock_function
    ):
        generate_gurb_invoice_base64_mock_function.return_value = (
            "JVBERi0xLjAKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUj4+"
            "ZW5kb2JqCjIgMCBvYmo8PC9UeXBlL1BhZ2VzL0tpZHNbMyAwIFJdL0NvdW50"
            "IDE+PmVuZG9iagozIDAgb2JqPDwvVHlwZS9QYWdlL1BhcmVudCAyIDAgUi9S"
            "ZXNvdXJjZXM8PD4+L01lZGlhQm94WzAgMCA5IDldPj5lbmRvYmoKeHJlZgow"
            "IDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAw"
            "MDAwMDAwNTIgMDAwMDAgbiAKMDAwMDAwMDEwMSAwMDAwMCBuIAp0cmFpbGVy"
            "PDwvUm9vdCAxIDAgUi9TaXplIDQ+PgpzdGFydHhyZWYKMTc0CiUlRU9G"
        )
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        invoice_o = self.openerp.pool.get("account.invoice")
        line_o = self.openerp.pool.get("account.invoice.line")
        self.maxDiff = None
        gurb_cups_id = self.get_references()["gurb_cups_id"]
        ctx = {"tpv": True}

        invoice_id, errs = gurb_cups_o.create_initial_invoice(
            self.cursor, self.uid, gurb_cups_id, context=ctx)

        self.assertFalse(errs)
        self.assertTrue(invoice_id)
        inv = invoice_o.read(self.cursor, self.uid, invoice_id)
        self._assert_partner_receivable_account(inv['partner_id'][0], inv['account_id'])
        self.assertEqual(inv['partner_id'][1], 'GISCE')
        self.assertEqual(inv['origin'], 'GURBCUPSID2')
        self.assertEqual(inv['reference'], 'GURBCUPSID2')
        self.assertEqual(inv['date_invoice'], datetime.today().strftime('%Y-%m-%d'))
        self.assertEqual(inv['amount_untaxed'], 3.75)
        self.assertEqual(inv['amount_tax'], 0.79)
        self.assertEqual(inv['amount_total'], 4.54)
        self.assertEqual(inv['type'], 'out_invoice')
        self.assertEqual(inv['state'], 'draft')
        self.assertEqual(len(inv['invoice_line']), 1)
        self.assertEqual(len(inv['tax_line']), 1)
        self.assertEqual(inv["residual"], 4.54)
        self.assertEqual(inv["saldo"], 4.54)
        self.assertEqual(inv['journal_id'][1], u'Factures GURB')
        self.assertEqual(inv['payment_type'][1], u'Cobrament Targeta')
        line = line_o.read(self.cursor, self.uid, inv['invoice_line'][0])
        self.assertEqual(line['name'], u"Cost d'adhesió GURB GRUP 001")
        self.assertEqual(line['quantity'], 1.0)
        self.assertEqual(line['price_unit'], 3.75)
        self._assert_account_code(line['account_id'], '705000000104')

    def test_pay_invoice_gurb(self):
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")
        invoice_o = self.openerp.pool.get("account.invoice")
        gurb_cups_id = self.get_references()["gurb_cups_id"]
        ctx = {"tpv": True}
        invoice_id, errs = gurb_cups_o.create_initial_invoice(
            self.cursor, self.uid, gurb_cups_id, context=ctx)
        self.assertFalse(errs)
        self.assertTrue(invoice_id)

        gurb_cups_o.pay_invoice_gurb(
            self.cursor, self.uid, invoice_id, context=ctx
        )

        inv = invoice_o.read(self.cursor, self.uid, invoice_id)
        self.assertEqual(inv['state'], 'paid')
        self.assertEqual(inv['residual'], 0.0)
        self.assertEqual(inv['saldo'], 4.54)
