# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import time
from datetime import date

from osv import osv
from tools.translate import _

try:
    unicode
except NameError:
    unicode = str


logger = logging.getLogger("openerp.{}".format(__name__))


class AccountInvoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"

    _redsys_failure_pending_state_ref = (
        "account_invoice_pending",
        "default_invoice_pending_state",
    )
    _redsys_recurrent_card_payment_type_code = "COBRAMENT_RECURRENT_TARGETA"
    _redsys_success_pending_reconcile_marker = (
        u"Redsys targeta recurrent OK pendent conciliacio"
    )
    _redsys_manual_review_marker = u"Redsys targeta recurrent pendent revisio"
    _redsys_failure_marker = u"Redsys targeta recurrent KO"

    def afegeix_a_remesa(self, cursor, uid, ids, order_id, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        blocked_invoice_names = []
        for invoice in self.browse(cursor, uid, ids, context=context):
            payment_type = getattr(invoice, "payment_type", False)
            if (
                payment_type
                and payment_type.code == self._redsys_recurrent_card_payment_type_code
            ):
                blocked_invoice_names.append(invoice.number or str(invoice.id))

        if blocked_invoice_names:
            raise osv.except_osv(
                _("Error"),
                _(
                    "No es poden afegir a una remesa les factures amb "
                    "cobrament recurrent per targeta. "
                    "Factures afectades: %s"
                )
                % ", ".join(blocked_invoice_names),
            )

        return super(AccountInvoice, self).afegeix_a_remesa(
            cursor, uid, ids, order_id, context=context
        )

    def _cron_collect_recurrent_card_invoices(self, cursor, uid, context=None):
        if context is None:
            context = {}

        for invoice_id in self._search_recurrent_card_invoice_ids(
            cursor, uid, context=context
        ):
            savepoint = self._redsys_invoice_savepoint_name(cursor, invoice_id)
            cursor.savepoint(savepoint)
            try:
                self._charge_invoice_by_redsys(
                    cursor, uid, invoice_id, context=context
                )
            except Exception:
                logger.exception(
                    "Unexpected Redsys recurrent card cron failure for invoice %s",
                    invoice_id,
                )
                cursor.rollback(savepoint)
                continue
            cursor.commit()

        return True

    def _redsys_invoice_savepoint_name(self, cursor, invoice_id):
        return "redsys_card_invoice_%s_%s" % (invoice_id, id(cursor))

    def _search_recurrent_card_invoice_ids(self, cursor, uid, limit=None, context=None):
        if context is None:
            context = {}

        payment_type_obj = self.pool.get("payment.type")
        payment_type_ids = payment_type_obj.search(
            cursor,
            uid,
            [("code", "=", self._redsys_recurrent_card_payment_type_code)],
            context=context,
        )
        if not payment_type_ids:
            return []

        today_str = date.today().strftime("%Y-%m-%d")
        invoice_ids = self.search(
            cursor,
            uid,
            [
                ("state", "=", "open"),
                ("type", "=", "out_invoice"),
                ("date_due", "<=", today_str),
                ("payment_order_id", "=", False),
                ("residual", ">", 0),
                ("payment_type", "in", payment_type_ids),
            ],
            limit=limit,
            context=context,
        )

        result = []
        factura_obj = self.pool.get("giscedata.facturacio.factura")
        factura_ids = factura_obj.search(
            cursor,
            uid,
            [("invoice_id", "in", invoice_ids), ("polissa_id", "!=", False)],
            context=context,
        )
        for factura in factura_obj.browse(cursor, uid, factura_ids, context=context):
            invoice = factura.invoice_id
            if self._has_redsys_success_pending_reconcile(invoice):
                continue
            if self._has_redsys_manual_review_pending(invoice):
                continue
            if self._has_redsys_failure_pending(invoice):
                continue
            if self._get_recurrent_card_for_invoice(cursor, uid, invoice, context=context):
                result.append(invoice.id)
        return result

    def _get_factura_for_invoice(self, cursor, uid, invoice, context=None):
        if context is None:
            context = {}

        factura_obj = self.pool.get("giscedata.facturacio.factura")
        factura_ids = factura_obj.search(
            cursor, uid, [("invoice_id", "=", invoice.id)], limit=1, context=context
        )
        if not factura_ids:
            return False
        return factura_obj.browse(cursor, uid, factura_ids[0], context=context)

    def _get_recurrent_card_for_invoice(self, cursor, uid, invoice, context=None):
        if context is None:
            context = {}

        factura = self._get_factura_for_invoice(cursor, uid, invoice, context=context)
        polissa = factura and getattr(factura, "polissa_id", False) or False
        if not polissa:
            return False

        card = getattr(polissa, "creditcard", False)
        if not card or not card.active or not card.token:
            return False

        pagador = getattr(polissa, "pagador", False)
        if pagador and card.partner_id.id != pagador.id:
            return False

        return card

    def _get_redsys_config(self, cursor, uid, context=None):
        if context is None:
            context = {}

        cfg_obj = self.pool.get("res.config")
        return {
            "merchant_code": cfg_obj.get(
                cursor, uid, "redsys_merchant_code", ""
            ),
            "private_key": cfg_obj.get(
                cursor, uid, "redsys_private_key", ""
            ),
            "merchant_url": cfg_obj.get(
                cursor, uid, "redsys_merchant_url", ""
            ),
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

    def _build_redsys_transaction_params(self, cursor, uid, invoice, card, context=None):
        if context is None:
            context = {}

        config = self._get_redsys_config(cursor, uid, context=context)
        amount_cents = str(int(round(invoice.residual * 100)))
        order_ref = self._build_redsys_order(invoice.id)
        invoice_ref = invoice.number or invoice.name or str(invoice.id)

        params = {
            "Ds_Merchant_Amount": amount_cents,
            "Ds_Merchant_Order": order_ref,
            "Ds_Merchant_MerchantCode": "%s" % config["merchant_code"],
            "Ds_Merchant_Currency": "%s" % config["currency"],
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Terminal": "%s" % config["terminal"],
            "Ds_Merchant_MerchantURL": "%s" % config["merchant_url"],
            "Ds_Merchant_SumTotal": amount_cents,
            "Ds_Merchant_Identifier": card.token,
            "Ds_Merchant_Cof_INI": "N",
            "Ds_Merchant_Cof_Type": "C",
            "Ds_Merchant_Excep_SCA": "MIT",
            "Ds_Merchant_DirectPayment": "true",
            "Ds_Merchant_PayMethods": "C",
            "Ds_Merchant_MerchantData": "invoice:%s" % invoice_ref,
        }
        return params, order_ref

    def _get_redsys_client(self, cursor, uid, context=None):
        if context is None:
            context = {}

        try:
            from sermepa import RestClient
        except ImportError:
            raise osv.except_osv(
                _("Error"),
                _(
                    "No s'ha pogut carregar la llibreria Sermepa. "
                    "Revisa que estigui disponible al runtime d'ERP."
                ),
            )

        config = self._get_redsys_config(cursor, uid, context=context)
        if not config["merchant_code"] or not config["private_key"]:
            raise osv.except_osv(
                _("Error"),
                _(
                    "Falta configurar el codi de comerç o la clau privada de Redsys."
                ),
            )

        return RestClient(
            config["merchant_code"],
            config["private_key"],
            endpoint_url=config["endpoint_url"],
            timeout=config["timeout"],
        )

    def _get_tpv_payment_data(self, cursor, uid, context=None):
        if context is None:
            context = {}

        cfg_obj = self.pool.get("res.config")
        journal_id = int(cfg_obj.get(cursor, uid, "redsys_tpv_journal_id", 0) or 0)
        journal_code = cfg_obj.get(cursor, uid, "redsys_tpv_journal_code", "")

        journal_obj = self.pool.get("account.journal")
        if not journal_id and journal_code:
            journal_ids = journal_obj.search(
                cursor, uid, [("code", "=", journal_code)], limit=1, context=context
            )
            journal_id = journal_ids and journal_ids[0] or False

        if not journal_id:
            raise osv.except_osv(
                _("Error"),
                _(
                    "Falta configurar el diari de cobrament TPV per Redsys "
                    "(redsys_tpv_journal_id o redsys_tpv_journal_code)."
                ),
            )

        journal_obj = self.pool.get("account.journal").browse(
            cursor, uid, journal_id, context=context
        )
        pay_account = journal_obj.default_credit_account_id or journal_obj.default_debit_account_id
        pay_account_id = pay_account and pay_account.id or False
        if not pay_account_id:
            raise osv.except_osv(
                _("Error"),
                _(
                    "Cal configurar un compte de crèdit o dèbit al diari "
                    "de cobrament TPV de Redsys."
                ),
            )

        period_ids = self.pool.get("account.period").find(
            cursor, uid, dt=date.today().strftime("%Y-%m-%d"), context=context
        )
        period_id = period_ids and period_ids[0] or False
        if not period_id:
            raise osv.except_osv(
                _("Error"),
                _("No s'ha trobat cap període comptable obert per cobrar Redsys."),
            )
        return {
            "journal_id": journal_id,
            "pay_account_id": pay_account_id,
            "period_id": period_id,
        }

    def _pay_invoice_by_tpv(self, cursor, uid, invoice, payment_data=None, context=None):
        if context is None:
            context = {}

        if payment_data is None:
            payment_data = self._get_tpv_payment_data(cursor, uid, context=context)
        pay_amount = invoice.residual
        if not pay_amount:
            return True

        pay_context = context.copy()
        pay_context.setdefault("date_p", date.today().strftime("%Y-%m-%d"))

        self.pay_and_reconcile(
            cursor,
            uid,
            [invoice.id],
            pay_amount,
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
        response_message = raw.get("error") or raw.get("message") or raw.get(
            "Ds_ErrorCode"
        )
        return response_code, response_message

    def _is_redsys_success(self, response_code):
        try:
            response_number = int("%s" % response_code)
        except (TypeError, ValueError):
            return False
        return 0 <= response_number <= 99

    def _get_redsys_failure_pending_state_id(self, cursor, uid, context=None):
        if context is None:
            context = {}

        return self.pool.get("ir.model.data").get_object_reference(
            cursor,
            uid,
            self._redsys_failure_pending_state_ref[0],
            self._redsys_failure_pending_state_ref[1],
        )[1]

    def _format_redsys_failure_note(
        self, invoice, order_ref, response_code, message, context=None
    ):
        if context is None:
            context = {}

        invoice_name = self._to_redsys_unicode(invoice.number or invoice.name or invoice.id)
        response_code_text = self._to_redsys_unicode(
            response_code if response_code is not None else "HTTP"
        )
        message_text = self._to_redsys_unicode(
            message if message is not None else _("Sense detall")
        )
        message_text = message_text.replace("\n", " ").replace("\r", " ").strip()
        if not message_text:
            message_text = self._to_redsys_unicode(_("Sense detall"))

        return (
            u"{} - Redsys targeta recurrent KO - factura {} - ordre {} - codi {} - {}".format(
                date.today().strftime("%Y-%m-%d"),
                invoice_name,
                order_ref,
                response_code_text,
                message_text,
            )
        )

    def _to_redsys_unicode(self, value):
        if value is None:
            return u""
        if isinstance(value, unicode):
            return value
        if isinstance(value, str):
            return value.decode("utf-8", "replace")
        return unicode(value)

    def _has_redsys_success_pending_reconcile(self, invoice):
        current_comment = self._to_redsys_unicode(
            getattr(invoice, "comment", False) or u""
        )
        return self._redsys_success_pending_reconcile_marker in current_comment

    def _is_redsys_invoice_lock_conflict(self, exc):
        return getattr(exc, "pgcode", False) == "55P03"

    def _lock_redsys_invoice_for_collection(self, cursor, uid, invoice_id, context=None):
        savepoint = "redsys_card_lock_%s_%s" % (invoice_id, id(cursor))
        cursor.savepoint(savepoint)
        try:
            cursor.execute(
                "SELECT id FROM account_invoice WHERE id = %s FOR UPDATE NOWAIT",
                (invoice_id,),
            )
        except Exception as exc:
            cursor.rollback(savepoint)
            if self._is_redsys_invoice_lock_conflict(exc):
                return False
            raise
        return True

    def _is_recurrent_card_invoice_still_collectable(self, invoice):
        if getattr(invoice, "state", "open") != "open":
            return False
        if getattr(invoice, "type", "out_invoice") != "out_invoice":
            return False
        if getattr(invoice, "payment_order_id", False):
            return False
        if getattr(invoice, "residual", 1) <= 0:
            return False

        due_date = getattr(invoice, "date_due", False)
        today_str = date.today().strftime("%Y-%m-%d")
        if due_date and due_date > today_str:
            return False

        payment_type = getattr(invoice, "payment_type", False)
        if not payment_type:
            return False
        if (
            getattr(payment_type, "code", False)
            != self._redsys_recurrent_card_payment_type_code
        ):
            return False
        return True

    def _redsys_success_reconcile_savepoint_name(self, cursor, invoice_id):
        return "redsys_card_success_reconcile_%s_%s" % (invoice_id, id(cursor))

    def _format_redsys_success_reconcile_note(self, invoice, order_ref, message):
        invoice_name = self._to_redsys_unicode(
            invoice.number or invoice.name or invoice.id
        )
        message_text = self._to_redsys_unicode(message or _("Sense detall"))
        message_text = message_text.replace("\n", " ").replace("\r", " ").strip()
        return (
            u"{} - {} - "
            u"factura {} - ordre {} - {}".format(
                date.today().strftime("%Y-%m-%d"),
                self._redsys_success_pending_reconcile_marker,
                invoice_name,
                self._to_redsys_unicode(order_ref),
                message_text,
            )
        )

    def _register_redsys_success_reconcile_failure(
        self, cursor, uid, invoice, order_ref, message, context=None
    ):
        if context is None:
            context = {}

        current_comment = self._to_redsys_unicode(
            getattr(invoice, "comment", False) or u""
        )
        if self._has_redsys_success_pending_reconcile(invoice):
            return False

        success_note = self._format_redsys_success_reconcile_note(
            invoice, order_ref, message
        )
        new_comment = success_note + (current_comment and u"\n" + current_comment or u"")
        self.write(cursor, uid, [invoice.id], {"comment": new_comment}, context=context)
        return True

    def _has_redsys_manual_review_pending(self, invoice):
        current_comment = self._to_redsys_unicode(
            getattr(invoice, "comment", False) or u""
        )
        return self._redsys_manual_review_marker in current_comment

    def _has_redsys_failure_pending(self, invoice):
        current_comment = self._to_redsys_unicode(
            getattr(invoice, "comment", False) or u""
        )
        return self._redsys_failure_marker in current_comment

    def _format_redsys_manual_review_note(self, invoice, order_ref, message):
        invoice_name = self._to_redsys_unicode(
            invoice.number or invoice.name or invoice.id
        )
        message_text = self._to_redsys_unicode(message or _("Sense detall"))
        message_text = message_text.replace("\n", " ").replace("\r", " ").strip()
        if not message_text:
            message_text = self._to_redsys_unicode(_("Sense detall"))

        return (
            u"{} - {} - factura {} - ordre {} - codi HTTP - {}".format(
                date.today().strftime("%Y-%m-%d"),
                self._redsys_manual_review_marker,
                invoice_name,
                self._to_redsys_unicode(order_ref),
                message_text,
            )
        )

    def _register_redsys_manual_review(
        self, cursor, uid, invoice, order_ref, message, context=None
    ):
        if context is None:
            context = {}

        current_comment = self._to_redsys_unicode(
            getattr(invoice, "comment", False) or u""
        )
        order_marker = u"ordre {}".format(self._to_redsys_unicode(order_ref))
        if (
            self._redsys_manual_review_marker in current_comment
            and order_marker in current_comment
        ):
            return False

        review_note = self._format_redsys_manual_review_note(
            invoice, order_ref, message
        )
        new_comment = review_note + (current_comment and u"\n" + current_comment or u"")
        self.write(cursor, uid, [invoice.id], {"comment": new_comment}, context=context)
        return False

    def _register_redsys_failure(
        self, cursor, uid, invoice, order_ref, response_code, message, context=None
    ):
        if context is None:
            context = {}

        target_pending_state_id = self._get_redsys_failure_pending_state_id(
            cursor, uid, context=context
        )
        current_pending_state_id = (
            invoice.pending_state and invoice.pending_state.id or False
        )
        response_code_text = self._to_redsys_unicode(
            response_code if response_code is not None else "HTTP"
        )
        marker = u"ordre {} - codi {}".format(order_ref, response_code_text)
        current_comment = self._to_redsys_unicode(invoice.comment or u"")

        if marker in current_comment:
            if current_pending_state_id != target_pending_state_id:
                self._set_redsys_failure_pending(
                    cursor,
                    uid,
                    invoice.id,
                    target_pending_state_id,
                    context=context,
                )
            return False

        failure_note = self._format_redsys_failure_note(
            invoice, order_ref, response_code_text, message, context=context
        )
        if current_comment:
            new_comment = failure_note + u"\n" + current_comment
        else:
            new_comment = failure_note

        self.write(
            cursor,
            uid,
            [invoice.id],
            {"comment": new_comment},
            context=context,
        )

        if current_pending_state_id != target_pending_state_id:
            self._set_redsys_failure_pending(
                cursor,
                uid,
                invoice.id,
                target_pending_state_id,
                context=context,
            )
        return True

    def _set_redsys_failure_pending(
        self, cursor, uid, invoice_id, pending_state_id, context=None
    ):
        if context is None:
            context = {}

        if hasattr(self, "set_pending"):
            return self.set_pending(
                cursor, uid, [invoice_id], pending_state_id, context=context
            )

        return self.write(
            cursor,
            uid,
            [invoice_id],
            {"pending_state": pending_state_id},
            context=context,
        )

    def _charge_invoice_by_redsys(self, cursor, uid, invoice_id, context=None):
        if context is None:
            context = {}

        if not self._lock_redsys_invoice_for_collection(
            cursor, uid, invoice_id, context=context
        ):
            return False

        invoice = self.browse(cursor, uid, invoice_id, context=context)
        if not self._is_recurrent_card_invoice_still_collectable(invoice):
            return False

        card = self._get_recurrent_card_for_invoice(cursor, uid, invoice, context=context)
        if not card:
            return False

        payment_data = self._get_tpv_payment_data(cursor, uid, context=context)
        params, order_ref = self._build_redsys_transaction_params(
            cursor, uid, invoice, card, context=context
        )
        client = self._get_redsys_client(cursor, uid, context=context)

        try:
            result = client.mit_payment(params)
        except Exception as exc:
            return self._register_redsys_manual_review(
                cursor,
                uid,
                invoice,
                order_ref,
                "%s" % exc,
                context=context,
            )

        response_code, response_message = self._extract_redsys_response_info(result)
        if self._is_redsys_success(response_code):
            savepoint = self._redsys_success_reconcile_savepoint_name(
                cursor, invoice_id
            )
            cursor.savepoint(savepoint)
            try:
                self._pay_invoice_by_tpv(
                    cursor, uid, invoice, payment_data=payment_data, context=context
                )
            except Exception as exc:
                cursor.rollback(savepoint)
                self._register_redsys_success_reconcile_failure(
                    cursor, uid, invoice, order_ref, "%s" % exc, context=context
                )
                return False
            return True

        return self._register_redsys_failure(
            cursor,
            uid,
            invoice,
            order_ref,
            response_code,
            response_message,
            context=context,
        )


AccountInvoice()
