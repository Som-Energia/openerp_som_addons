# -*- coding: utf-8 -*-
from __future__ import absolute_import

import time
from decimal import Decimal, ROUND_HALF_UP

from osv import osv, fields
from tools.translate import _


class CardPaymentAttempt(osv.osv):
    _name = "som.card.payment.attempt"
    _description = "Intent de cobrament recurrent amb targeta"
    _rec_name = "order_ref"

    _state_selection = [
        ("submitted", "Enviat a Redsys"),
        ("approved", "Cobrat"),
        ("declined", "Denegat"),
        ("review", "Pendent de revisio"),
        ("reconcile_failed", "Cobrat pendent de conciliacio"),
    ]

    _columns = {
        "invoice_id": fields.many2one(
            "account.invoice", "Factura", required=True, ondelete="cascade", select=True
        ),
        "card_id": fields.many2one(
            "res.partner.creditcard", "Targeta", required=True, ondelete="restrict"
        ),
        "order_ref": fields.char("Ordre Redsys", size=12, required=True, select=True),
        "amount_cents": fields.integer("Import en centims", required=True),
        "currency": fields.char("Moneda", size=4, required=True),
        "state": fields.selection(
            _state_selection, "Estat", required=True, readonly=True, select=True
        ),
        "response_code": fields.char("Codi Redsys", size=16, readonly=True),
        "response_message": fields.text("Resposta Redsys", readonly=True),
    }

    _sql_constraints = [
        (
            "som_card_payment_attempt_order_ref_unique",
            "unique (order_ref)",
            "L'ordre de Redsys ja existeix.",
        )
    ]

    _blocking_states = [
        "submitted",
        "approved",
        "declined",
        "review",
        "reconcile_failed",
    ]

    def _get_redsys_config(self, cursor, uid, context=None):
        cfg_obj = self.pool.get("res.config")
        return {
            "merchant_code": cfg_obj.get(cursor, uid, "redsys_merchant_code", ""),
            "private_key": cfg_obj.get(cursor, uid, "redsys_private_key", ""),
            "merchant_url": cfg_obj.get(cursor, uid, "redsys_merchant_url", ""),
            "endpoint_url": cfg_obj.get(
                cursor,
                uid,
                "redsys_endpoint_url",
                "https://sis.redsys.es/sis/rest/trataPeticionREST",
            ),
            "terminal": cfg_obj.get(cursor, uid, "redsys_terminal", "1"),
            "currency": cfg_obj.get(cursor, uid, "redsys_currency", "978"),
            "timeout": int(cfg_obj.get(cursor, uid, "redsys_timeout", 30)),
        }

    def _to_base36(self, number, width):
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        number = abs(int(number))
        chars = []
        while number:
            number, remainder = divmod(number, 36)
            chars.append(alphabet[remainder])
        value = "".join(reversed(chars)) or "0"
        return value[-width:].rjust(width, "0")

    def _build_redsys_order(self, invoice_id):
        timestamp = int(time.time() * 1000000)
        suffix = self._to_base36(timestamp + int(invoice_id), 8)
        return "%04d%s" % (invoice_id % 10000, suffix)

    def _build_redsys_transaction_params(
        self, cursor, uid, invoice, card, order_ref=None, context=None
    ):
        config = self._get_redsys_config(cursor, uid, context=context)
        amount_cents = str(
            int(
                (Decimal(str(invoice.residual)) * Decimal("100")).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
        )
        order_ref = order_ref or self._build_redsys_order(invoice.id)
        invoice_ref = invoice.number or invoice.name or str(invoice.id)
        return {
            "Ds_Merchant_Amount": amount_cents,
            "Ds_Merchant_Order": order_ref,
            "Ds_Merchant_MerchantCode": "%s" % config["merchant_code"],
            "Ds_Merchant_Currency": "%s" % config["currency"],
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Terminal": "%s" % config["terminal"],
            "Ds_Merchant_MerchantURL": "%s" % config["merchant_url"],
            "Ds_Merchant_SumTotal": amount_cents,
            "Ds_Merchant_Identifier": card.token,
            "Ds_Merchant_Cof_TxnID": card.cof_txnid,
            "Ds_Merchant_Cof_INI": "N",
            "Ds_Merchant_Cof_Type": "C",
            "Ds_Merchant_Excep_SCA": "MIT",
            "Ds_Merchant_DirectPayment": "true",
            "Ds_Merchant_PayMethods": "C",
            "Ds_Merchant_MerchantData": "invoice:%s" % invoice_ref,
        }, order_ref

    def _get_redsys_client(self, cursor, uid, context=None):
        try:
            from sermepa import RestClient
        except ImportError:
            raise osv.except_osv(
                _("Error"),
                _("No s'ha pogut carregar la llibreria Sermepa. Revisa el runtime."),
            )

        config = self._get_redsys_config(cursor, uid, context=context)
        if not config["merchant_code"] or not config["private_key"]:
            raise osv.except_osv(
                _("Error"),
                _("Falta configurar el codi de comerç o la clau privada de Redsys."),
            )
        return RestClient(
            config["merchant_code"],
            config["private_key"],
            endpoint_url=config["endpoint_url"],
            timeout=config["timeout"],
        )

    def _extract_redsys_response_info(self, result):
        result = result or {}
        merchant_params = result.get("merchant_parameters") or {}
        raw = result.get("raw") or {}
        response_code = (
            merchant_params.get("Ds_Response")
            or raw.get("Ds_Response")
            or raw.get("Ds_ErrorCode")
            or raw.get("error")
            or raw.get("message")
        )
        return response_code, raw.get("error") or raw.get("message") or raw.get(
            "Ds_ErrorCode"
        )

    def _is_redsys_success(self, response_code):
        try:
            return 0 <= int("%s" % response_code) <= 99
        except (TypeError, ValueError):
            return False

    def has_blocking_attempt(self, cursor, uid, invoice_id, context=None):
        return bool(
            self.search(
                cursor,
                uid,
                [("invoice_id", "=", invoice_id), ("state", "in", self._blocking_states)],
                limit=1,
                context=context,
            )
        )

    def _lock_invoice(self, cursor, invoice_id):
        savepoint = "redsys_card_lock_%s_%s" % (invoice_id, id(cursor))
        cursor.savepoint(savepoint)
        try:
            cursor.execute(
                "SELECT id FROM account_invoice WHERE id = %s FOR UPDATE NOWAIT",
                (invoice_id,),
            )
        except Exception as exc:
            cursor.rollback(savepoint)
            if getattr(exc, "pgcode", False) == "55P03":
                return False
            raise
        return True

    def _set_state(self, cursor, uid, attempt_id, state, code=None, message=None, context=None):
        values = {"state": state}
        if code is not None:
            values["response_code"] = "%s" % code
        if message is not None:
            values["response_message"] = "%s" % message
        return self.write(cursor, uid, [attempt_id], values, context=context)

    def charge_invoice(self, cursor, uid, invoice_id, context=None):
        context = context or {}
        invoice_obj = self.pool.get("account.invoice")
        if not self._lock_invoice(cursor, invoice_id):
            return False

        invoice = invoice_obj.browse(cursor, uid, invoice_id, context=context)
        if not invoice_obj._is_recurrent_card_invoice_still_collectable(invoice):
            return False
        if self.has_blocking_attempt(cursor, uid, invoice.id, context=context):
            return False

        card = invoice_obj._get_recurrent_card_for_invoice(
            cursor, uid, invoice, context=context
        )
        if not card:
            return False

        payment_data = invoice_obj._get_tpv_payment_data(cursor, uid, context=context)
        config = self._get_redsys_config(cursor, uid, context=context)
        order_ref = self._build_redsys_order(invoice.id)
        amount_cents = int(
            (Decimal(str(invoice.residual)) * Decimal("100")).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        attempt_id = self.create(
            cursor,
            uid,
            {
                "invoice_id": invoice.id,
                "card_id": card.id,
                "order_ref": order_ref,
                "amount_cents": amount_cents,
                "currency": config["currency"],
                "state": "submitted",
            },
            context=context,
        )
        params, order_ref = self._build_redsys_transaction_params(
            cursor, uid, invoice, card, order_ref=order_ref, context=context
        )
        try:
            result = self._get_redsys_client(cursor, uid, context=context).mit_payment(params)
            response_code, response_message = self._extract_redsys_response_info(result)
        except Exception as exc:
            self._set_state(cursor, uid, attempt_id, "review", "HTTP", exc, context)
            return True

        if self._is_redsys_success(response_code):
            savepoint = "redsys_card_success_reconcile_%s_%s" % (invoice_id, id(cursor))
            cursor.savepoint(savepoint)
            try:
                invoice_obj._pay_invoice_by_tpv(
                    cursor, uid, invoice, payment_data=payment_data, context=context
                )
            except Exception as exc:
                cursor.rollback(savepoint)
                self._set_state(cursor, uid, attempt_id, "reconcile_failed",
                                message=exc, context=context)
                return True
            self._set_state(cursor, uid, attempt_id, "approved", context=context)
            return True

        self._set_state(
            cursor,
            uid,
            attempt_id,
            "declined",
            response_code or "HTTP",
            response_message or _("Sense detall"),
            context,
        )
        pending_state_id = invoice_obj._get_redsys_failure_pending_state_id(
            cursor, uid, context=context
        )
        if not invoice.pending_state or invoice.pending_state.id != pending_state_id:
            invoice_obj._set_redsys_failure_pending(
                cursor, uid, invoice.id, pending_state_id, context=context
            )
        return True


CardPaymentAttempt()
