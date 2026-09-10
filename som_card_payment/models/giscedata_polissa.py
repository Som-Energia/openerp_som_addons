# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import date

from osv import osv, fields


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    _recurring_card_payment_type_code = "COBRAMENT_RECURRENT_TARGETA"

    def _recurring_card_result(self, card, policy, invoices, today, reason_code=False):
        policy_changed = policy["disposition"] == "updated"
        invoice_changed = bool(invoices["migrated"])
        partial = bool(invoices["remitted"] or invoices["failed"])
        if partial:
            status = "partial"
            reason_code = reason_code or "invoice_excluded_or_failed"
        elif not policy_changed and not invoice_changed:
            status = "no-op"
            reason_code = reason_code or "already_converted"
        else:
            status = "complete"
            reason_code = reason_code or "converted"
        return {
            "status": status,
            "reason_code": reason_code,
            "card": card,
            "policy": policy,
            "invoices": invoices,
        }

    def _recurring_card_payment_ids(self, cursor, uid, context=None):
        imd_obj = self.pool.get("ir.model.data")
        payment_type_id = imd_obj.get_object_reference(
            cursor, uid, "som_card_payment", "payment_type_card_recurrent"
        )[1]
        payment_mode_id = imd_obj.get_object_reference(
            cursor, uid, "som_card_payment", "payment_mode_card_recurrent"
        )[1]
        return payment_type_id, payment_mode_id

    def convert_to_recurring_card(self, cursor, uid, polissa_id, card_data, context=None):
        context = (context or {}).copy()
        today = date.today().strftime("%Y-%m-%d")
        self.check_perm(cursor, uid, "write", context=context)
        polissa = self.browse(cursor, uid, polissa_id, context=context)
        empty_invoices = {"migrated": [], "remitted": [], "failed": [], "unchanged": []}
        if not polissa.pagador or polissa.state != "activa":
            return self._recurring_card_result(
                {"id": False, "disposition": "unchanged"},
                {"id": polissa_id, "disposition": "unchanged", "effective_date": today},
                empty_invoices,
                today,
                "policy_not_eligible",
            )
        payment_type_id, payment_mode_id = self._recurring_card_payment_ids(
            cursor, uid, context=context
        )
        current_card = polissa.creditcard
        equivalent_card = bool(
            current_card
            and current_card.active
            and current_card.partner_id.id == polissa.pagador.id
            and all(
                getattr(current_card, field) == card_data.get(field)
                for field in ("token", "masked_number", "expiry_date", "cof_txnid")
            )
        )
        already_converted = bool(
            equivalent_card
            and polissa.tipo_pago
            and polissa.tipo_pago.id == payment_type_id
            and polissa.payment_mode_id
            and polissa.payment_mode_id.id == payment_mode_id
        )
        if already_converted:
            factura_obj = self.pool.get("giscedata.facturacio.factura")
            invoices = factura_obj.migrate_recurring_card_invoices(
                cursor, uid, polissa_id, payment_type_id, today, context=context
            )
            return self._recurring_card_result(
                {"id": current_card.id, "disposition": "reused"},
                {"id": polissa_id, "disposition": "unchanged", "effective_date": today},
                invoices,
                today=today,
                reason_code="already_converted",
            )

        self.check_modifiable_polissa(cursor, uid, polissa_id, context=context)

        card_result = self.pool.get("res.partner.creditcard").resolve_for_payer(
            cursor, uid, polissa.pagador.id, card_data, context=context
        )
        modcontractual_obj = self.pool.get("giscedata.polissa.modcontractual")
        modcontractual_obj.check_perm(cursor, uid, "create", context=context)
        current_modcon = getattr(polissa, "modcontractual_activa", False)
        end_date = current_modcon and current_modcon.data_final or False
        self.crear_modcon(
            cursor,
            uid,
            polissa_id,
            {
                "tipo_pago": payment_type_id,
                "payment_mode_id": payment_mode_id,
                "creditcard": card_result["id"],
            },
            today,
            end_date,
            context=context,
        )
        invoices = self.pool.get(
            "giscedata.facturacio.factura"
        ).migrate_recurring_card_invoices(
            cursor, uid, polissa_id, payment_type_id, today, context=context
        )
        return self._recurring_card_result(
            card_result,
            {"id": polissa_id, "disposition": "updated", "effective_date": today},
            invoices,
            today,
        )

    def onchange_tipo_pago(self, cursor, uid, ids, tipo_pago, pagador, context=None):
        res = super(GiscedataPolissa, self).onchange_tipo_pago(
            cursor, uid, ids, tipo_pago, pagador, context=context
        )
        res.setdefault("value", {})
        if not tipo_pago:
            res["value"].update({"creditcard": False})
            return res

        payment_type = self.pool.get("payment.type").browse(cursor, uid, tipo_pago, context=context)
        if payment_type.code != "COBRAMENT_RECURRENT_TARGETA":
            res["value"].update({"creditcard": False})
            return res

        if not pagador:
            res.setdefault("value", {}).update({"creditcard": False})
            return res

        card_obj = self.pool.get("res.partner.creditcard")
        card_ids = card_obj.search(cursor, uid, [("partner_id", "=", pagador)], context=context)
        res["value"].update({"creditcard": card_ids[0] if len(card_ids) == 1 else False})
        return res

    def _check_card_payment_data(self, cursor, uid, ids, context=None):
        for polissa in self.browse(cursor, uid, ids, context=context):
            if not polissa.tipo_pago or polissa.tipo_pago.code != "COBRAMENT_RECURRENT_TARGETA":
                continue
            if not polissa.creditcard:
                return False
            if polissa.creditcard.partner_id.id != polissa.pagador.id:
                return False
        return True

    _columns = {
        "creditcard": fields.many2one(
            "res.partner.creditcard",
            "Targeta",
            ondelete="restrict",
            readonly=True,
            states={
                "esborrany": [("readonly", False)],
                "validar": [("readonly", False)],
                "modcontractual": [("readonly", False)],
            },
        ),
    }

    _constraints = [
        (
            _check_card_payment_data,
            "Cal indicar una targeta del pagador quan el tipus de pagament "
            "es cobrament recurrent per targeta.",
            ["tipo_pago", "creditcard", "pagador"],
        )
    ]


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    def _check_card_payment_data(self, cursor, uid, ids, context=None):
        for modcontractual in self.browse(cursor, uid, ids, context=context):
            payment_type = getattr(modcontractual, "tipo_pago", False)
            if not payment_type or payment_type.code != "COBRAMENT_RECURRENT_TARGETA":
                continue

            creditcard = getattr(modcontractual, "creditcard", False)
            if not creditcard:
                return False

            pagador = getattr(modcontractual, "pagador", False)
            if not pagador and getattr(modcontractual, "polissa_id", False):
                pagador = modcontractual.polissa_id.pagador
            if pagador and creditcard.partner_id.id != pagador.id:
                return False

        return True

    _columns = {
        "creditcard": fields.many2one("res.partner.creditcard", "Targeta", ondelete="restrict"),
    }

    _constraints = [
        (
            _check_card_payment_data,
            "Cal indicar una targeta del pagador quan el tipus de pagament "
            "es cobrament recurrent per targeta.",
            ["tipo_pago", "creditcard", "pagador"],
        )
    ]


GiscedataPolissaModcontractual()
