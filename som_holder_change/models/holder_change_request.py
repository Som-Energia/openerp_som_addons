# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64
import pooler
from datetime import datetime
from uuid import uuid4

import netsvc

from osv import fields, osv
from tools.translate import _


IMMUTABLE_FIELDS = frozenset([
    "polissa_id",
    "cups",
    "owner_change_type",
    "payload",
])

REQUEST_STATES = [
    ("received", "Received"),
    ("awaiting_payment", "Awaiting payment"),
    ("validation_error", "Validation error"),
    ("awaiting_signature", "Awaiting signature"),
    ("queued", "Queued"),
    ("completed", "Completed"),
    ("execution_error", "Execution error"),
]

STATE_TRANSITIONS = {
    "received": ("awaiting_payment", "awaiting_signature", "validation_error"),
    "awaiting_payment": ("awaiting_signature",),
    "awaiting_signature": ("queued",),
    "queued": ("completed", "execution_error"),
}


class SomHolderChangeRequest(osv.osv):
    _name = "som.holder.change.request"
    _description = "Holder change request"
    _rec_name = "cups"

    def _one_id(self, ids):
        if isinstance(ids, (list, tuple)):
            if len(ids) != 1:
                raise osv.except_osv(_("Invalid holder change"),
                                     _("Exactly one request is required."))
            return ids[0]
        return ids

    def _needs_new_contract(self, cursor, uid, request, context=None):
        if request.owner_change_type == "T":
            return True
        return bool(int(self.pool.get("res.config").get(
            cursor, uid, "sw_m1_owner_change_subrogacio_new_contract", "1"
        )))

    def _payment_method(self, request):
        return request.payload.get("payment_method", "bank")

    def _reserve_references(self, cursor, uid, request_id, context=None):
        request = self.browse(cursor, uid, request_id, context=context)
        values = {}
        if (
            self._needs_new_contract(cursor, uid, request, context=context)
            and not request.contract_number
        ):
            values["contract_number"] = self.pool.get("ir.sequence").get(
                cursor, uid, "giscedata.polissa"
            )
        if self._payment_method(request) == "bank" and not request.mandate_number:
            values["mandate_number"] = uuid4().hex
        if values:
            super(SomHolderChangeRequest, self).write(
                cursor, uid, [request_id], values, context=context
            )

    def _create_holder(self, cursor, uid, request, context=None):
        holder = request.payload["holder"]
        vat = holder["vat"].upper()
        if not vat.startswith("ES"):
            vat = "ES{}".format(vat)
        values = {
            "name": holder["name"],
            "vat": vat,
            "lang": request.polissa_id.titular.lang,
        }
        return self.pool.get("res.partner").create(cursor, uid, values, context=context)

    def _payment_values(self, cursor, uid, request, partner_id, temporary=False, context=None):
        if self._payment_method(request) == "card":
            card_data = {
                "token": request.creditcard_token or "validation-token-{}".format(request.id),
                "masked_number": request.creditcard_masked_number or "**** **** **** 0000",
                "expiry_date": request.creditcard_expiry_date or "12/30",
                "cof_txnid": request.creditcard_cof_txnid or "validation-cof-{}".format(request.id),
            }
            card_id = self.pool.get("res.partner.creditcard").create(
                cursor, uid, dict(card_data, partner_id=partner_id), context=context
            )
            imd_obj = self.pool.get("ir.model.data")
            return {
                "payment_mode_id": imd_obj.get_object_reference(
                    cursor, uid, "som_card_payment", "payment_mode_card_recurrent"
                )[1],
                "tipo_pago": imd_obj.get_object_reference(
                    cursor, uid, "som_card_payment", "payment_type_card_recurrent"
                )[1],
                "creditcard": card_id,
            }

        iban = request.payload["payment"]["iban"].replace(" ", "")
        bank_id = self.pool.get("res.partner.bank").create(
            cursor,
            uid,
            {"partner_id": partner_id, "iban": iban, "state": "iban"},
            context=context,
        )
        contract = request.polissa_id
        return {
            "bank": bank_id,
            "payment_mode_id": contract.payment_mode_id.id,
            "tipo_pago": contract.tipo_pago.id,
        }

    def _m1_values(self, cursor, uid, request, partner_id, payment_values, context=None):
        vat_kind = self.pool.get("res.partner").get_vat_type(
            cursor, uid, partner_id, context=context
        )
        values = {
            "change_atr": False,
            "change_adm": True,
            "owner_change_type": request.owner_change_type,
            "generate_new_contract": "create" if self._needs_new_contract(
                cursor, uid, request, context=context
            ) else "exists",
            "change_retail_tariff": False,
            "retail_tariff": False,
            "activacio_cicle": "A",
            "owner": partner_id,
            "pagador": partner_id,
            "contact": partner_id,
            "cnae": request.polissa_id.cnae.id,
            "vat": request.payload["holder"]["vat"],
            "vat_kind": vat_kind,
            "direccio_pagament": request.polissa_id.direccio_pagament.id,
            "direccio_notificacio": request.polissa_id.direccio_notificacio.id,
        }
        values.update(payment_values)
        if values["generate_new_contract"] == "exists":
            values["new_contract"] = False
        return values

    def _run_m1(self, cursor, uid, request, partner_id, payment_values, context=None):
        m1_payment_values = payment_values.copy()
        is_card_payment = bool(m1_payment_values.pop("creditcard", None))
        if is_card_payment:
            # M1 cannot create a recurrent-card contract because it validates the
            # payment before the card can be assigned to the copied contract.
            m1_payment_values.update({
                "bank": request.polissa_id.bank.id,
                "payment_mode_id": request.polissa_id.payment_mode_id.id,
                "tipo_pago": request.polissa_id.tipo_pago.id,
            })
        values = self._m1_values(
            cursor, uid, request, partner_id, m1_payment_values, context=context
        )
        execution_context = (context or {}).copy()
        extra_values = {}
        if request.contract_number:
            extra_values["name"] = request.contract_number
        if extra_values:
            execution_context["new_contract_extra_vals"] = extra_values
        switching_ids = self.pool.get("giscedata.polissa").generate_M1_API(
            cursor, uid, request.polissa_id.id, values, context=execution_context
        )
        if len(switching_ids) != 1:
            raise osv.except_osv(
                _("M1 generation failed"),
                _("The holder change did not generate exactly one M1 case."),
            )
        switching = self.pool.get("giscedata.switching").browse(
            cursor, uid, switching_ids[0], context=context
        )
        polissa_id = switching.polissa_ref_id.id
        if is_card_payment:
            self.pool.get("giscedata.polissa").write(
                cursor,
                uid,
                polissa_id,
                {
                    "payment_mode_id": payment_values["payment_mode_id"],
                    "tipo_pago": payment_values["tipo_pago"],
                    "creditcard": payment_values["creditcard"],
                },
                context=context,
            )
        return switching_ids[0], polissa_id

    def _create_mandate(self, cursor, uid, request, partner_id, polissa_id, context=None):
        if self._payment_method(request) != "bank":
            return False
        payment_mode = request.polissa_id.payment_mode_id
        mandate_obj = self.pool.get("payment.mandate")
        mandate_scheme = getattr(payment_mode, "mandate_scheme", False) or "core"
        mandate_id = mandate_obj.create(
            cursor,
            uid,
            {
                "name": request.mandate_number,
                "reference": "giscedata.polissa,{}".format(polissa_id),
                "mandate_scheme": mandate_scheme,
            },
            context=context,
        )
        mandate_obj.update_from_reference(
            cursor, uid, [mandate_id], context=context
        )
        mandate_obj.write(
            cursor,
            uid,
            [mandate_id],
            {
                "name": request.mandate_number,
                "date": datetime.today().strftime("%Y-%m-%d"),
                "mandate_scheme": mandate_scheme,
                "debtor_iban": request.payload["payment"]["iban"].replace(" ", ""),
            },
            context=context,
        )
        return mandate_id

    def _render_reports(self, cursor, uid, request, polissa_id, mandate_id, context=None):
        contract_pdf, _format = netsvc.LocalService(
            "report.giscedata.polissa.contract.summary.full"
        ).create(cursor, uid, [polissa_id], {}, context=context)
        result = {"contract_pdf": base64.b64encode(contract_pdf)}
        if mandate_id:
            mandate_pdf, _format = netsvc.LocalService("report.report_mandato").create(
                cursor, uid, [mandate_id], {}, context=context
            )
            result["mandate_pdf"] = base64.b64encode(mandate_pdf)
        return result

    def prepare(self, cursor, uid, request_id, context=None):
        request_id = self._one_id(request_id)
        self._reserve_references(cursor, uid, request_id, context=context)
        # The isolated simulation cursor must see the stable reserved references.
        cursor.commit()
        request = self.browse(cursor, uid, request_id, context=context)
        temporary_cursor = pooler.get_db(cursor.dbname).cursor()
        temporary_context = (context or {}).copy()
        temporary_context["in_rollback_transaction"] = True
        try:
            request = self.browse(temporary_cursor, uid, request_id, context=temporary_context)
            partner_id = self._create_holder(
                temporary_cursor, uid, request, context=temporary_context)
            payment_values = self._payment_values(
                temporary_cursor,
                uid,
                request,
                partner_id,
                temporary=True,
                context=temporary_context,
            )
            switching_id, polissa_id = self._run_m1(
                temporary_cursor,
                uid,
                request,
                partner_id,
                payment_values,
                context=temporary_context,
            )
            mandate_id = self._create_mandate(
                temporary_cursor, uid, request, partner_id, polissa_id, context=temporary_context
            )
            reports = self._render_reports(
                temporary_cursor, uid, request, polissa_id, mandate_id, context=temporary_context
            )
        finally:
            temporary_cursor.rollback()
            temporary_cursor.close()

        state = "awaiting_payment" if self._payment_method(
            request) == "card" and not request.creditcard_token else "awaiting_signature"
        super(SomHolderChangeRequest, self).write(
            cursor,
            uid,
            [request_id],
            dict(reports, state=state, error_code=False, error_message=False),
            context=context,
        )
        return True

    def set_card_data(self, cursor, uid, request_id, card_values, context=None):
        request_id = self._one_id(request_id)
        request = self.browse(cursor, uid, request_id, context=context)
        if self._payment_method(request) != "card":
            raise osv.except_osv(_("Invalid payment method"), _(
                "The request does not use card payment."))
        if request.state != "awaiting_payment" or request.creditcard_token:
            raise osv.except_osv(_("Card data rejected"), _(
                "Card data cannot be changed for this request."))
        required = ("creditcard_token", "creditcard_masked_number",
                    "creditcard_expiry_date", "creditcard_cof_txnid")
        missing = [field for field in required if not card_values.get(field)]
        if missing:
            raise osv.except_osv(_("Invalid card data"), _(
                "Missing card fields: {}.").format(", ".join(missing)))
        super(SomHolderChangeRequest, self).write(
            cursor,
            uid,
            [request_id],
            {field: card_values[field] for field in required},
            context=context,
        )
        return self.prepare(cursor, uid, request_id, context=context)

    def execute(self, cursor, uid, request_id, context=None):
        request_id = self._one_id(request_id)
        request = self.browse(cursor, uid, request_id, context=context)
        if request.state == "completed":
            return {
                "switching_id": request.switching_id.id,
                "result_polissa_id": request.result_polissa_id.id,
            }
        if request.state != "queued":
            raise osv.except_osv(
                _("Invalid request state"), _("The request has not been signed.")
            )
        super(SomHolderChangeRequest, self).write(
            cursor,
            uid,
            [request_id],
            {
                "attempt_count": request.attempt_count + 1,
                "last_attempt_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            context=context,
        )
        partner_id = self._create_holder(cursor, uid, request, context=context)
        payment_values = self._payment_values(cursor, uid, request, partner_id, context=context)
        switching_id, polissa_id = self._run_m1(
            cursor, uid, request, partner_id, payment_values, context=context)
        self._create_mandate(cursor, uid, request, partner_id, polissa_id, context=context)
        super(SomHolderChangeRequest, self).write(
            cursor,
            uid,
            [request_id],
            {
                "state": "completed",
                "switching_id": switching_id,
                "result_polissa_id": polissa_id,
            },
            context=context,
        )
        return {"switching_id": switching_id, "result_polissa_id": polissa_id}

    def write(self, cursor, uid, ids, values, context=None):
        immutable = IMMUTABLE_FIELDS.intersection(values)
        if immutable:
            raise osv.except_osv(
                _("Immutable request"),
                _("The holder change request identity and payload cannot be modified."),
            )
        if "state" in values:
            for request in self.browse(cursor, uid, ids, context=context):
                if values["state"] == request.state:
                    continue
                allowed = STATE_TRANSITIONS.get(request.state, ())
                if values["state"] not in allowed:
                    raise osv.except_osv(
                        _("Invalid request state"),
                        _("The request state transition is not allowed."),
                    )
        return super(SomHolderChangeRequest, self).write(
            cursor, uid, ids, values, context=context
        )

    _columns = {
        "polissa_id": fields.many2one(
            "giscedata.polissa",
            "Contract",
            required=True,
            readonly=True,
            ondelete="restrict",
        ),
        "cups": fields.char(
            "CUPS", size=22, required=True, readonly=True, select=True
        ),
        "owner_change_type": fields.selection(
            [("T", "Transfer"), ("S", "Subrogation")],
            "Holder change type",
            required=True,
            readonly=True,
        ),
        "payload": fields.json("Request payload", required=True, readonly=True),
        "contract_number": fields.char("Reserved contract number", size=64, readonly=True),
        "mandate_number": fields.char("Reserved mandate number", size=64, readonly=True),
        "contract_pdf": fields.binary("Simulated contract", readonly=True),
        "mandate_pdf": fields.binary("Simulated mandate", readonly=True),
        "creditcard_token": fields.char("Card token", size=256, readonly=True),
        "creditcard_masked_number": fields.char("Masked card number", size=32, readonly=True),
        "creditcard_expiry_date": fields.char("Card expiry date", size=16, readonly=True),
        "creditcard_cof_txnid": fields.char("Card COF transaction", size=128, readonly=True),
        "state": fields.selection(
            REQUEST_STATES, "State", required=True, readonly=True, select=True
        ),
        "signature_process_id": fields.many2one(
            "giscedata.signatura.process",
            "Signature process",
            readonly=True,
            ondelete="restrict",
        ),
        "switching_id": fields.many2one(
            "giscedata.switching",
            "M1 case",
            readonly=True,
            ondelete="restrict",
        ),
        "result_polissa_id": fields.many2one(
            "giscedata.polissa",
            "Result contract",
            readonly=True,
            ondelete="restrict",
        ),
        "attempt_count": fields.integer("Execution attempts", readonly=True),
        "last_attempt_at": fields.datetime("Last attempt", readonly=True),
        "error_code": fields.char("Error code", size=64, readonly=True),
        "error_message": fields.text("Error message", readonly=True),
    }

    _defaults = {
        "state": lambda *args: "received",
        "attempt_count": lambda *args: 0,
    }

    _order = "id desc"


SomHolderChangeRequest()
