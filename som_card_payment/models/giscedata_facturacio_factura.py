# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import time
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from osv import osv, fields
from tools.translate import _


logger = logging.getLogger("openerp.{}".format(__name__))


class GiscedataFacturacioFactura(osv.osv):
    _name = "giscedata.facturacio.factura"
    _inherit = "giscedata.facturacio.factura"

    _redsys_failure_pending_state_ref = (
        "account_invoice_pending",
        "default_invoice_pending_state",
    )
    _redsys_recurrent_card_payment_type_code = "COBRAMENT_RECURRENT_TARGETA"
    _redsys_collection_states = [
        ("submitted", "Enviat a Redsys"),
        ("paid", "Cobrat"),
        ("declined", "Denegat"),
        ("review", "Pendent de revisio"),
    ]

    def _is_recurrent_card_payment(self, cursor, uid, ids, name, arg, context=None):
        result = {}
        for factura in self.browse(cursor, uid, ids, context=context):
            result[factura.id] = bool(
                factura.payment_type
                and factura.payment_type.code
                == self._redsys_recurrent_card_payment_type_code
            )
        return result

    _columns = {
        "is_recurrent_card_payment": fields.function(
            _is_recurrent_card_payment,
            method=True,
            type="boolean",
            string="Cobrament recurrent per targeta",
        ),
        "redsys_collection_state": fields.selection(
            _redsys_collection_states, "Estat cobrament Redsys", readonly=True
        ),
        "redsys_order_ref": fields.char("Ordre Redsys", size=12, readonly=True),
        "redsys_card_id": fields.many2one(
            "res.partner.creditcard", "Targeta Redsys", readonly=True
        ),
        "redsys_amount_cents": fields.integer("Import Redsys en centims", readonly=True),
        "redsys_currency": fields.char("Moneda Redsys", size=4, readonly=True),
        "redsys_response_code": fields.char("Codi Redsys", size=16, readonly=True),
        "redsys_response_message": fields.text("Resposta Redsys", readonly=True),
    }

    def _cron_collect_recurrent_card_factures(self, cursor, uid, context=None):
        context = context or {}
        for factura_id in self._search_recurrent_card_factura_ids(
            cursor, uid, context=context
        ):
            try:
                processed = self._charge_factura_by_redsys(
                    cursor, uid, factura_id, context=context
                )
            except Exception:
                logger.exception(
                    "Unexpected Redsys recurrent card cron failure for factura %s",
                    factura_id,
                )
                cursor.rollback()
                continue
            if processed:
                cursor.commit()
            else:
                cursor.rollback()
        return True

    def _search_recurrent_card_factura_ids(self, cursor, uid, limit=None, context=None):
        context = context or {}
        payment_type_ids = self.pool.get("payment.type").search(
            cursor,
            uid,
            [("code", "=", self._redsys_recurrent_card_payment_type_code)],
            context=context,
        )
        if not payment_type_ids:
            return []
        return self.search(
            cursor,
            uid,
            [
                ("state", "=", "open"),
                ("type", "=", "out_invoice"),
                ("date_due", "<=", date.today().strftime("%Y-%m-%d")),
                ("payment_order_id", "=", False),
                ("invoice_id.residual", ">", 0),
                ("payment_type", "in", payment_type_ids),
                ("polissa_id", "!=", False),
                ("redsys_collection_state", "in", [False, "submitted"]),
            ],
            limit=limit,
            context=context,
        )

    def _get_recurrent_card_for_factura(self, cursor, uid, factura, context=None):
        polissa = getattr(factura, "polissa_id", False)
        if not polissa:
            return False
        card = getattr(polissa, "creditcard", False)
        if not card or not card.active or not card.token or not card.cof_txnid:
            return False
        pagador = getattr(polissa, "pagador", False)
        if pagador and card.partner_id.id != pagador.id:
            return False
        return card

    def _get_redsys_config(self, cursor, uid, context=None):
        cfg_obj = self.pool.get("res.config")
        return {
            "merchant_code": cfg_obj.get(cursor, uid, "redsys_merchant_code", ""),
            "private_key": cfg_obj.get(cursor, uid, "redsys_private_key", ""),
            "merchant_url": cfg_obj.get(cursor, uid, "redsys_merchant_url", ""),
            "endpoint_url": cfg_obj.get(
                cursor, uid, "redsys_endpoint_url",
                "https://sis.redsys.es/sis/rest/trataPeticionREST"
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
        return ("".join(reversed(chars)) or "0")[-width:].rjust(width, "0")

    def _build_redsys_order(self, invoice_id):
        return "%04d%s" % (
            invoice_id % 10000,
            self._to_base36(int(time.time() * 1000000) + int(invoice_id), 8),
        )

    def _build_redsys_transaction_params(
        self, cursor, uid, factura, card, order_ref=None, context=None
    ):
        invoice = factura.invoice_id
        config = self._get_redsys_config(cursor, uid, context=context)
        amount_cents = str(
            int((Decimal(str(invoice.residual)) * Decimal("100")).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            ))
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
            config["merchant_code"], config["private_key"],
            endpoint_url=config["endpoint_url"], timeout=config["timeout"]
        )

    def _extract_redsys_response_info(self, result):
        result = result or {}
        merchant_params = result.get("merchant_parameters") or {}
        raw = result.get("raw") or {}
        return (
            merchant_params.get("Ds_Response") or raw.get("Ds_Response")
            or raw.get("Ds_ErrorCode") or raw.get("error") or raw.get("message"),
            raw.get("error") or raw.get("message") or raw.get("Ds_ErrorCode"),
        )

    def _is_redsys_success(self, response_code):
        try:
            return 0 <= int("%s" % response_code) <= 99
        except (TypeError, ValueError):
            return False

    def _get_tpv_payment_data(self, cursor, uid, context=None):
        cfg_obj = self.pool.get("res.config")
        journal_key = "redsys_tpv_journal_id"
        pay_account_key = "redsys_tpv_pay_account_id"
        try:
            journal_id = int(cfg_obj.get(cursor, uid, journal_key, 0) or 0)
            if journal_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            raise osv.except_osv(
                _("Error"),
                _("Cal configurar un ID positiu vàlid per %(key)s.") % {
                    "key": journal_key,
                },
            )
        try:
            pay_account_id = int(
                cfg_obj.get(cursor, uid, pay_account_key, 0) or 0
            )
            if pay_account_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            raise osv.except_osv(
                _("Error"),
                _("Cal configurar un ID positiu vàlid per %(key)s.") % {
                    "key": pay_account_key,
                },
            )
        journal_obj = self.pool.get("account.journal")
        journal_ids = journal_obj.search(
            cursor, uid, [("id", "=", journal_id)], context=context
        )
        if not journal_ids:
            raise osv.except_osv(
                _("Error"),
                _("No existeix cap diari per %(key)s.") % {"key": journal_key},
            )
        account_obj = self.pool.get("account.account")
        pay_account_ids = account_obj.search(
            cursor, uid, [("id", "=", pay_account_id)], context=context
        )
        if not pay_account_ids:
            raise osv.except_osv(
                _("Error"),
                _("No existeix cap compte per %(key)s.") % {
                    "key": pay_account_key,
                },
            )
        period_ids = self.pool.get("account.period").find(
            cursor, uid, dt=date.today().strftime("%Y-%m-%d"), context=context
        )
        if not period_ids:
            raise osv.except_osv(
                _("Error"),
                _("No s'ha trobat cap període comptable obert per cobrar Redsys."),
            )
        return {
            "journal_id": journal_id,
            "pay_account_id": pay_account_id,
            "period_id": period_ids[0],
        }

    def _pay_invoice_by_tpv(self, cursor, uid, invoice, payment_data=None, context=None):
        if not invoice.residual:
            return True
        payment_data = payment_data or self._get_tpv_payment_data(cursor, uid, context)
        pay_context = (context or {}).copy()
        pay_context.setdefault("date_p", date.today().strftime("%Y-%m-%d"))
        self.pool.get("account.invoice").pay_and_reconcile(
            cursor,
            uid,
            [invoice.id],
            invoice.residual,
            payment_data["pay_account_id"],
            payment_data["period_id"],
            payment_data["journal_id"],
            False,
            payment_data["period_id"],
            False,
            context=pay_context,
            name=invoice.number or invoice.name or str(invoice.id),
        )
        return True

    def _get_redsys_failure_pending_state_id(self, cursor, uid, context=None):
        return self.pool.get("ir.model.data").get_object_reference(
            cursor, uid, *self._redsys_failure_pending_state_ref
        )[1]

    def _is_recurrent_card_factura_still_collectable(self, factura):
        if factura.state != "open" or factura.type != "out_invoice":
            return False
        if factura.payment_order_id or factura.invoice_id.residual <= 0:
            return False
        if factura.date_due and factura.date_due > date.today().strftime("%Y-%m-%d"):
            return False
        return bool(
            factura.payment_type
            and factura.payment_type.code == self._redsys_recurrent_card_payment_type_code
        )

    def _charge_factura_by_redsys(self, cursor, uid, factura_id, context=None):
        context = context or {}
        factura = self.browse(cursor, uid, factura_id, context=context)
        invoice_id = factura.invoice_id.id
        lock_savepoint = "redsys_card_lock_%s_%s" % (invoice_id, id(cursor))
        cursor.savepoint(lock_savepoint)
        try:
            cursor.execute(
                "SELECT id FROM account_invoice WHERE id = %s FOR UPDATE NOWAIT",
                (invoice_id,),
            )
        except Exception as exc:
            cursor.rollback(lock_savepoint)
            if getattr(exc, "pgcode", False) == "55P03":
                return False
            raise

        factura = self.browse(cursor, uid, factura_id, context=context)
        if factura.redsys_collection_state == "submitted":
            self.write(
                cursor,
                uid,
                [factura.id],
                {
                    "redsys_collection_state": "review",
                    "redsys_response_message": (
                        "Redsys request result is unknown for order %s. "
                        "Manual reconciliation is required; the request was not retried."
                        % (factura.redsys_order_ref or "unknown")
                    ),
                },
                context=context,
            )
            return True
        if (
            not self._is_recurrent_card_factura_still_collectable(factura)
            or factura.redsys_collection_state
        ):
            return False
        card = self._get_recurrent_card_for_factura(cursor, uid, factura, context=context)
        if not card:
            return False

        invoice = factura.invoice_id
        config = self._get_redsys_config(cursor, uid, context=context)
        order_ref = self._build_redsys_order(invoice.id)
        amount_cents = int(
            (Decimal(str(invoice.residual)) * Decimal("100")).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        payment_data = self._get_tpv_payment_data(cursor, uid, context=context)
        params, order_ref = self._build_redsys_transaction_params(
            cursor, uid, factura, card, order_ref=order_ref, context=context
        )
        redsys_client = self._get_redsys_client(cursor, uid, context=context)
        self.write(
            cursor,
            uid,
            [factura.id],
            {
                "redsys_collection_state": "submitted",
                "redsys_order_ref": order_ref,
                "redsys_card_id": card.id,
                "redsys_amount_cents": amount_cents,
                "redsys_currency": config["currency"],
                "redsys_response_code": False,
                "redsys_response_message": False,
            },
            context=context,
        )
        # The durable submitted marker prevents a second cron run from charging twice.
        cursor.commit()

        factura = self.browse(cursor, uid, factura_id, context=context)
        invoice = factura.invoice_id
        try:
            result = redsys_client.mit_payment(params)
            response_code, response_message = self._extract_redsys_response_info(result)
        except Exception as exc:
            self.write(
                cursor,
                uid,
                [factura.id],
                {
                    "redsys_collection_state": "review",
                    "redsys_response_code": "HTTP",
                    "redsys_response_message": "%s" % exc,
                },
                context=context,
            )
            return True

        if self._is_redsys_success(response_code):
            savepoint = "redsys_card_success_reconcile_%s_%s" % (invoice.id, id(cursor))
            cursor.savepoint(savepoint)
            try:
                self._pay_invoice_by_tpv(
                    cursor, uid, invoice, payment_data=payment_data, context=context
                )
            except Exception as exc:
                cursor.rollback(savepoint)
                self.write(
                    cursor,
                    uid,
                    [factura.id],
                    {
                        "redsys_collection_state": "review",
                        "redsys_response_message": "%s" % exc,
                    },
                    context=context,
                )
                return True
            self.write(
                cursor,
                uid,
                [factura.id],
                {
                    "redsys_collection_state": "paid",
                    "redsys_response_code": "%s" % response_code,
                    "redsys_response_message": response_message or False,
                },
                context=context,
            )
            return True

        self.write(
            cursor,
            uid,
            [factura.id],
            {
                "redsys_collection_state": "declined",
                "redsys_response_code": "%s" % (response_code or "HTTP"),
                "redsys_response_message": "%s" % (response_message or _("Sense detall")),
            },
            context=context,
        )
        pending_state_id = self._get_redsys_failure_pending_state_id(
            cursor, uid, context=context
        )
        if not invoice.pending_state or invoice.pending_state.id != pending_state_id:
            self.set_pending(cursor, uid, [factura.id], pending_state_id, context=context)
        return True


GiscedataFacturacioFactura()
