# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from datetime import date

from osv import osv, fields
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
    _columns = {
        "redsys_attempt_ids": fields.one2many(
            "som.card.payment.attempt", "invoice_id", "Intents Redsys", readonly=True
        ),
    }

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
                processed = self._charge_invoice_by_redsys(
                    cursor, uid, invoice_id, context=context
                )
            except Exception:
                logger.exception(
                    "Unexpected Redsys recurrent card cron failure for invoice %s",
                    invoice_id,
                )
                cursor.rollback(savepoint)
                continue
            if processed:
                cursor.commit()
            else:
                cursor.rollback(savepoint)

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
        seen_invoice_ids = set()
        factura_obj = self.pool.get("giscedata.facturacio.factura")
        factura_ids = factura_obj.search(
            cursor,
            uid,
            [("invoice_id", "in", invoice_ids), ("polissa_id", "!=", False)],
            context=context,
        )
        factura_invoice_ids = set()
        for factura in factura_obj.browse(cursor, uid, factura_ids, context=context):
            invoice = factura.invoice_id
            factura_invoice_ids.add(invoice.id)
            if invoice.id in seen_invoice_ids:
                continue
            seen_invoice_ids.add(invoice.id)
            if self._has_any_redsys_collection_marker(cursor, uid, invoice.id, context):
                continue
            if self._get_recurrent_card_for_invoice(cursor, uid, invoice, context=context):
                result.append(invoice.id)
        missing_factura_invoice_ids = sorted(set(invoice_ids) - factura_invoice_ids)
        if missing_factura_invoice_ids:
            logger.debug(
                "Skipping Redsys recurrent card invoices without linked factura: %s",
                missing_factura_invoice_ids,
            )
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
        if not card or not card.active or not card.token or not card.cof_txnid:
            return False

        pagador = getattr(polissa, "pagador", False)
        if pagador and card.partner_id.id != pagador.id:
            return False

        return card

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

    def _get_redsys_failure_pending_state_id(self, cursor, uid, context=None):
        if context is None:
            context = {}

        return self.pool.get("ir.model.data").get_object_reference(
            cursor,
            uid,
            self._redsys_failure_pending_state_ref[0],
            self._redsys_failure_pending_state_ref[1],
        )[1]

    def _has_any_redsys_collection_marker(self, cursor, uid, invoice_id, context=None):
        return self.pool.get("som.card.payment.attempt").has_blocking_attempt(
            cursor, uid, invoice_id, context=context
        )

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
        return self.pool.get("som.card.payment.attempt").charge_invoice(
            cursor, uid, invoice_id, context=context
        )


AccountInvoice()
