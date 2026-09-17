# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64
import json
import logging
import pooler
from datetime import datetime
from uuid import uuid4


import netsvc

from osv import fields, osv
from tools.translate import _

from . import holder_change_payload


logger = logging.getLogger(__name__)


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

    def prepare(self, cursor, uid, request_id, context=None):
        request_id = self._one_id(request_id)
        self._reserve_references(cursor, uid, request_id, context=context)
        # The isolated simulation cursor must see the stable reserved references.
        cursor.commit()
        reports = self._simulate_holder_change(cursor, uid, request_id, context=context)
        request = self.browse(cursor, uid, request_id, context=context)
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
        # Queue retries can run concurrently; serialize them before inspecting state.
        cursor.execute(
            "SELECT id FROM som_holder_change_request WHERE id = %s FOR UPDATE",
            (request_id,),
        )
        request = self.browse(cursor, uid, request_id, context=context)
        if request.state == "completed":
            self._notify_completed_request(cursor, uid, request_id, context=context)
            return {
                "switching_id": request.switching_id.id,
                "result_polissa_id": request.result_polissa_id.id,
            }
        if request.state != "queued":
            raise osv.except_osv(
                _("Invalid request state"), _("The request has not been signed."))
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
        switching_id, polissa_id, _mandate_id, new_member_partner_id = self._run_holder_change(
            cursor, uid, request, context=context
        )
        super(SomHolderChangeRequest, self).write(
            cursor,
            uid,
            [request_id],
            {
                "state": "completed",
                "switching_id": switching_id,
                "result_polissa_id": polissa_id,
                "new_member_partner_id": new_member_partner_id,
            },
            context=context,
        )
        self._notify_completed_request(cursor, uid, request_id, context=context)
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

    def _simulate_holder_change(self, cursor, uid, request_id, context=None):
        request = self.browse(cursor, uid, request_id, context=context)
        temporary_cursor = pooler.get_db(cursor.dbname).cursor()
        temporary_context = (context or {}).copy()
        temporary_context["in_rollback_transaction"] = True
        try:
            request = self.browse(temporary_cursor, uid, request_id, context=temporary_context)
            switching_id, polissa_id, mandate_id, _new_member_partner_id = self._run_holder_change(
                temporary_cursor,
                uid,
                request,
                temporary=True,
                context=temporary_context,
            )
            reports = self._render_reports(
                temporary_cursor, uid, request, polissa_id, mandate_id, context=temporary_context
            )
        finally:
            temporary_cursor.rollback()
            temporary_cursor.close()
        return reports

    def _run_holder_change(self, cursor, uid, request, temporary=False, context=None):
        change_data = self._prepare_change_data(
            cursor, uid, request, temporary=temporary, context=context
        )
        execution = self._execute_m1_change(
            cursor, uid, request, change_data, context=context
        )
        self._apply_result_contract_membership(
            cursor, uid, execution["polissa_id"], change_data, context=context
        )
        new_member_partner_id = change_data["is_new_member"] and change_data["partner_id"]
        return (
            execution["switching_id"],
            execution["polissa_id"],
            execution["mandate_id"],
            new_member_partner_id,
        )

    def _prepare_change_data(self, cursor, uid, request, temporary=False, context=None):
        nocutoff_id = False
        if request.payload["especial_cases"].get("reason_electrodep"):
            nocutoff_id = self._indispensable_nocutoff_id(cursor, uid, context=context)
        partner_id = self._create_holder(cursor, uid, request, context=context)
        address_id = self._create_holder_address(
            cursor, uid, request, partner_id, context=context
        )
        member_partner_id, is_new_member, is_ct_ss_member = self._member_partner(
            cursor, uid, request, partner_id, context=context
        )
        payment_values = self._payment_values(
            cursor, uid, request, partner_id, temporary=temporary, context=context
        )
        return {
            "address_id": address_id,
            "is_ct_ss_member": is_ct_ss_member,
            "is_new_member": is_new_member,
            "member_partner_id": member_partner_id,
            "nocutoff_id": nocutoff_id,
            "partner_id": partner_id,
            "payment_values": payment_values,
        }

    def _execute_m1_change(self, cursor, uid, request, change_data, context=None):
        switching_id, polissa_id = self._run_m1(
            cursor,
            uid,
            request,
            change_data["partner_id"],
            change_data["address_id"],
            change_data["payment_values"],
            context=context,
        )
        mandate_id = self._create_mandate(
            cursor, uid, request, change_data["partner_id"], polissa_id, context=context
        )
        self._apply_post_m1_effects(
            cursor,
            uid,
            request,
            switching_id,
            change_data["partner_id"],
            change_data["member_partner_id"],
            change_data["address_id"],
            change_data["payment_values"],
            context=context,
        )
        self._apply_special_documents(
            cursor,
            uid,
            request,
            change_data["partner_id"],
            polissa_id,
            nocutoff_id=change_data["nocutoff_id"],
            context=context,
        )
        return {
            "mandate_id": mandate_id,
            "polissa_id": polissa_id,
            "switching_id": switching_id,
        }

    def _apply_result_contract_membership(
        self, cursor, uid, polissa_id, change_data, context=None
    ):
        member_partner_id = change_data["member_partner_id"]
        if member_partner_id:
            values = {"soci": member_partner_id}
            if change_data["is_ct_ss_member"]:
                category_id = self.pool.get("ir.model.data").get_object_reference(
                    cursor,
                    uid,
                    "som_polissa_soci",
                    "origen_ct_sense_socia_category",
                )[1]
                values["category_id"] = [(4, category_id)]
            self.pool.get("giscedata.polissa").write(
                cursor, uid, polissa_id, values, context=context
            )
        if change_data["is_new_member"]:
            self.pool.get("res.partner").adopt_contracts_as_member(
                cursor, uid, change_data["partner_id"], context=context
            )

    def _run_m1(self, cursor, uid, request, partner_id, address_id, payment_values, context=None):
        m1_payment_values, is_card_payment = self._m1_payment_values(
            request, payment_values
        )
        values = self._m1_values(
            cursor, uid, request, partner_id, address_id, m1_payment_values, context=context
        )
        execution_context = (context or {}).copy()
        extra_values = {}
        signature_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        if request.owner_change_type == "T":
            self.pool.get("giscedata.polissa").write(
                cursor,
                uid,
                polissa_id,
                {"data_firma_contracte": signature_date},
                context=context,
            )
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

    def _m1_payment_values(self, request, payment_values):
        values = payment_values.copy()
        is_card_payment = bool(values.pop("creditcard", None))
        if is_card_payment:
            # M1 cannot validate the recurrent card before the copied contract exists.
            values.update({
                "bank": request.polissa_id.bank.id,
                "payment_mode_id": request.polissa_id.payment_mode_id.id,
                "tipo_pago": request.polissa_id.tipo_pago.id,
            })
        return values, is_card_payment

    def _m1_values(
        self, cursor, uid, request, partner_id, address_id, payment_values, context=None
    ):
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
            "activacio_cicle": "L",
            "owner": partner_id,
            "pagador": partner_id,
            "contact": partner_id,
            "cnae": request.polissa_id.cnae.id,
            "vat": request.payload["holder"]["vat"],
            "vat_kind": vat_kind,
            "direccio_pagament": address_id,
            "direccio_notificacio": address_id,
        }
        wizard_obj = self.pool.get("giscedata.switching.mod.con.wizard")
        values.update(wizard_obj.get_partner_fields(cursor, uid, partner_id, "con"))
        values.update(wizard_obj.get_phone(cursor, uid, address_id))
        values.update(payment_values)
        if values["generate_new_contract"] == "exists":
            values["new_contract"] = request.polissa_id.id
        return values

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

    def _apply_post_m1_effects(
        self,
        cursor,
        uid,
        request,
        switching_id,
        partner_id,
        member_partner_id,
        address_id,
        payment_values,
        context=None,
    ):
        switching_obj = self.pool.get("giscedata.switching")
        polissa_obj = self.pool.get("giscedata.polissa")
        partner = self.pool.get("res.partner").browse(
            cursor, uid, partner_id, context=context
        )
        address = self.pool.get("res.partner.address").browse(
            cursor, uid, address_id, context=context
        )
        member = member_partner_id and self.pool.get("res.partner").browse(
            cursor, uid, member_partner_id, context=context
        ) or False
        iban = "-"
        if payment_values.get("bank"):
            iban = self.pool.get("res.partner.bank").browse(
                cursor, uid, payment_values["bank"], context=context
            ).iban
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # TODO: Revisar i actualitzar observacions
        observation = (
            "-- webforms diu: --\n"
            "****Canvi de titular amb soci vinculat ({} {})****\n"
            "Data de petició: {}\nNou Titular: {}\nNIF: {}\n"
            "Contacte: {} {}\nIBAN: {}\n-- webforms ha dit --"
        ).format(
            member and member.name or "-",
            member and member.ref or "-",
            timestamp,
            partner.name,
            partner.vat[2:],
            address.email or "",
            address.phone or address.mobile or "",
            iban,
        )
        old_polissa = polissa_obj.browse(
            cursor, uid, request.polissa_id.id, context=context
        )
        polissa_obj.write(
            cursor,
            uid,
            request.polissa_id.id,
            {
                "no_estimable": True,
                "observacions_estimacio": holder_change_payload.append_observation(
                    old_polissa.observacions_estimacio,
                    "\n(webforms)[{}] Canvi de titular".format(timestamp),
                ),
                "observacions": holder_change_payload.append_observation(
                    old_polissa.observacions, observation),
            },
            context=context,
        )
        switching = switching_obj.browse(cursor, uid, switching_id, context=context)
        payload = json.dumps(request.payload, sort_keys=True, indent=2)
        switching_obj.write(
            cursor,
            uid,
            switching_id,
            {
                "state": "draft" if request.owner_change_type == "S" else "open",
                "user_observations": holder_change_payload.append_observation(
                    switching.user_observations, payload
                ),
            },
            context=context,
        )

    def _create_holder(self, cursor, uid, request, context=None):
        holder = request.payload["holder"]
        vat = holder_change_payload.normalize_holder_vat(holder)
        partner_obj = self.pool.get("res.partner")
        values = {
            "name": holder_change_payload.holder_full_name(holder),
            "vat": vat,
            "lang": self._holder_language(cursor, uid, request, context=context),
        }
        if not holder_change_payload.is_individual_holder(holder):
            values["comment"] = " Persona representant: {}\n NIF representant: {}".format(
                holder["proxyname"], holder["proxynif"]
            )
        partner_ids = partner_obj.search(
            cursor, uid, [("vat", "=", vat)], limit=1, context=context
        )
        if partner_ids:
            return partner_ids[0]
        return partner_obj.create(cursor, uid, values, context=context)

    def _holder_language(self, cursor, uid, request, context=None):
        language = request.payload["holder"]["language"]
        language_ids = self.pool.get("res.lang").search(
            cursor, uid, [("code", "=", language)], limit=1, context=context
        )
        return language if language_ids else request.polissa_id.titular.lang

    def _create_holder_address(self, cursor, uid, request, partner_id, context=None):
        holder = request.payload["holder"]
        iban = holder_change_payload.clean_iban(request.payload["payment"].get("iban", ""))
        country_id = iban and self._iban_country(cursor, uid, iban, context=context) or False
        address_obj = self.pool.get("res.partner.address")
        address_ids = address_obj.search(
            cursor,
            uid,
            [("partner_id", "=", partner_id), ("nv", "=", holder["address"])],
            limit=1,
            context=context,
        )
        if address_ids:
            return address_ids[0]
        values = {
            "partner_id": partner_id,
            "name": holder_change_payload.holder_full_name(holder),
            "nv": holder["address"],
            "zip": holder["postal_code"],
            "id_municipi": holder["city"],
            "id_poblacio": self._get_or_create_poblacio(
                cursor, uid, holder["city"], context=context
            ),
            "state_id": holder["state"],
            "country_id": country_id,
            "email": holder["email"],
            "phone": holder["phone1"],
        }
        return address_obj.create(cursor, uid, values, context=context)

    def _iban_country(self, cursor, uid, iban, context=None):
        country_ids = self.pool.get("res.country").search(
            cursor, uid, [("code", "=", iban[:2])], limit=1, context=context
        )
        if not country_ids:
            raise osv.except_osv(_("Invalid IBAN"), _("The IBAN country is invalid."))
        return country_ids[0]

    def _get_or_create_poblacio(self, cursor, uid, municipi_id, context=None):
        poblacio_obj = self.pool.get("res.poblacio")
        municipi = self.pool.get("res.municipi").browse(
            cursor, uid, municipi_id, context=context
        )
        poblacio_ids = poblacio_obj.search(
            cursor,
            uid,
            [("municipi_id", "=", municipi_id), ("name", "=", municipi.name)],
            limit=1,
            context=context,
        )
        return poblacio_ids[0] if poblacio_ids else poblacio_obj.create(
            cursor,
            uid,
            {"municipi_id": municipi_id, "name": municipi.name},
            context=context,
        )

    def _member_partner(self, cursor, uid, request, holder_id, context=None):
        member = request.payload["member"]
        if member.get("link_member"):
            return self._linked_member_partner(cursor, uid, member, context=context), False, False
        if member.get("become_member"):
            existing_member_ids = self.pool.get("somenergia.soci").search(
                cursor,
                uid,
                [("partner_id", "=", holder_id)],
                limit=1,
                context=context,
            )
            if existing_member_ids:
                return holder_id, False, False
            self.pool.get("res.partner").become_member(
                cursor, uid, holder_id, context=context
            )
            return holder_id, True, False
        ct_ss_member_id = self.pool.get("ir.model.data").get_object_reference(
            cursor, uid, "som_polissa_soci", "res_partner_soci_ct"
        )[1]
        return ct_ss_member_id, False, True

    def _linked_member_partner(self, cursor, uid, member, context=None):
        vat = holder_change_payload.normalize_holder_vat(member)
        member_ids = self.pool.get("somenergia.soci").search(
            cursor, uid, [("vat", "=", vat)], context=context
        )
        for member_record in self.pool.get("somenergia.soci").browse(
            cursor, uid, member_ids, context=context
        ):
            if member_record.www_soci == member["number"]:
                return member_record.partner_id.id
        raise osv.except_osv(
            _("Member not found"), _("The linked member does not exist or is inactive.")
        )

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

        iban = holder_change_payload.clean_iban(request.payload["payment"]["iban"])
        bank_obj = self.pool.get("res.partner.bank")
        if not bank_obj.is_iban_valid(cursor, uid, iban):
            raise osv.except_osv(_("Invalid IBAN"), _("The IBAN is invalid."))
        country_id = self._iban_country(cursor, uid, iban, context=context)
        bank_ids = bank_obj.search(
            cursor,
            uid,
            [("partner_id", "=", partner_id), ("iban", "=", iban)],
            limit=1,
            context=context,
        )
        if bank_ids:
            bank_id = bank_ids[0]
        else:
            onchange = bank_obj.onchange_banco(
                cursor, uid, [], iban[4:].encode("ascii"), country_id, context or {}
            )
            if "value" not in onchange:
                raise osv.except_osv(
                    _("Invalid IBAN"),
                    onchange.get("warning", {}).get("message", _("The IBAN is invalid.")),
                )
            values = onchange["value"]
            values.update({
                "state": "iban",
                "iban": iban,
                "partner_id": partner_id,
                "country_id": country_id,
                "acc_country_id": country_id,
                "state_id": request.payload["holder"]["state"],
            })
            bank_id = bank_obj.create(cursor, uid, values, context=context)
        contract = request.polissa_id
        return {
            "bank": bank_id,
            "payment_mode_id": contract.payment_mode_id.id,
            "tipo_pago": contract.tipo_pago.id,
        }

    def _apply_special_documents(
        self,
        cursor,
        uid,
        request,
        partner_id,
        polissa_id,
        nocutoff_id=False,
        context=None,
    ):
        cases = request.payload["especial_cases"]
        category_code, description = holder_change_payload.special_case_document_spec(cases)
        target_model = "giscedata.polissa"
        target_id = polissa_id
        if cases.get("reason_electrodep"):
            target_id = self._get_or_create_electrodependency_document(
                cursor, uid, partner_id, polissa_id, context=context
            )
            target_model = "som.documents.sensibles"
            self.pool.get("giscedata.polissa").write(
                cursor,
                uid,
                polissa_id,
                {"nocutoff": nocutoff_id or self._indispensable_nocutoff_id(
                    cursor, uid, context=context
                )},
                context=context,
            )
        if not category_code:
            return

        self._copy_special_case_attachments(
            cursor,
            uid,
            request,
            category_code,
            description,
            target_model,
            target_id,
            context=context,
        )

    def _get_or_create_electrodependency_document(
        self, cursor, uid, partner_id, polissa_id, context=None
    ):
        category_id = self.pool.get("ir.model.data").get_object_reference(
            cursor,
            uid,
            "som_documents_sensibles",
            "documents_sensibles_category_electrodependent",
        )[1]
        document_obj = self.pool.get("som.documents.sensibles")
        document_ids = document_obj.search(
            cursor,
            uid,
            [("partner_id", "=", partner_id), ("categoria", "=", category_id)],
            context=context,
        )
        if document_ids:
            return document_ids[0]
        today = datetime.today().strftime("%Y-%m-%d")
        return document_obj.create(
            cursor,
            uid,
            {
                "name": self.pool.get("giscedata.polissa").read(
                    cursor, uid, polissa_id, ["name"], context=context
                )["name"],
                "data_recepcio": today,
                "darrera_data_valida": today,
                "partner_id": partner_id,
                "categoria": category_id,
            },
            context=context,
        )

    def _indispensable_nocutoff_id(self, cursor, uid, context=None):
        nocutoff_ids = self.pool.get("giscedata.polissa.nocutoff").search(
            cursor, uid, [("motiu", "like", "imprescindible")], limit=1, context=context
        )
        if not nocutoff_ids:
            raise osv.except_osv(
                _("Missing no-cutoff reason"),
                _("The indispensable supply no-cutoff reason is required."),
            )
        return nocutoff_ids[0]

    def _copy_special_case_attachments(
        self,
        cursor,
        uid,
        request,
        category_code,
        description,
        target_model,
        target_id,
        context=None,
    ):
        attachment_obj = self.pool.get("ir.attachment")
        attachment_ids = attachment_obj.search(
            cursor,
            uid,
            [
                ("res_model", "=", "som.holder.change.request"),
                ("res_id", "=", request.id),
            ],
            context=context,
        )
        for attachment in attachment_obj.browse(cursor, uid, attachment_ids, context=context):
            if attachment.category_id.code != category_code:
                continue
            copied_ids = attachment_obj.search(
                cursor,
                uid,
                [
                    ("res_model", "=", target_model),
                    ("res_id", "=", target_id),
                    ("category_id", "=", attachment.category_id.id),
                    ("datas_fname", "=", attachment.datas_fname),
                    ("description", "=", description),
                ],
                context=context,
            )
            if any(copied.datas == attachment.datas for copied in attachment_obj.browse(
                cursor, uid, copied_ids, context=context
            )):
                continue
            attachment_obj.create(
                cursor,
                uid,
                {
                    "name": attachment.name,
                    "datas": attachment.datas,
                    "datas_fname": attachment.datas_fname,
                    "category_id": attachment.category_id.id,
                    "description": description,
                    "res_model": target_model,
                    "res_id": target_id,
                },
                context=context,
            )

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

    def _notify_completed_request(self, cursor, uid, request_id, context=None):
        request = self.browse(cursor, uid, request_id, context=context)
        for notification in self._completed_notification_specs(
            cursor, uid, request, context=context
        ):
            try:
                self._send_mail(
                    cursor,
                    uid,
                    notification["module"],
                    notification["xml_id"],
                    notification["model"],
                    notification["record_id"],
                    notification["recipient"],
                    from_email=notification["from_email"],
                    context=context,
                )
            except Exception as error:
                logger.exception("Unable to send holder change notification: %s", error)
                continue
            super(SomHolderChangeRequest, self).write(
                cursor, uid, [request_id], {notification["field"]: True}, context=context
            )

    def _completed_notification_specs(self, cursor, uid, request, context=None):
        switching = request.switching_id
        pas = switching.get_pas()
        notifications = []
        if not request.owner_notification_sent:
            notifications.append({
                "field": "owner_notification_sent",
                "module": "giscedata_switching" if request.owner_change_type == "T"
                else "som_polissa_condicions_generals",
                "xml_id": "notification_atr_M1_01" if request.owner_change_type == "T"
                else "notification_atr_M1_01_SS",
                "model": "giscedata.switching",
                "record_id": switching.id,
                "recipient": pas.direccio_notificacio.email,
                "from_email": "modifica@somenergia.coop",
            })
        if not request.old_owner_notification_sent:
            notifications.append({
                "field": "old_owner_notification_sent",
                "module": "som_switching",
                "xml_id": "email_validacio_dades_canvi_titular",
                "model": "giscedata.switching",
                "record_id": switching.id,
                "recipient": switching.mail_pagador_polissa,
                "from_email": "modifica@somenergia.coop",
            })
        if request.new_member_partner_id and not request.member_notification_sent:
            member_ids = self.pool.get("somenergia.soci").search(
                cursor,
                uid,
                [("partner_id", "=", request.new_member_partner_id.id)],
                limit=1,
                context=context,
            )
            if member_ids:
                notifications.append({
                    "field": "member_notification_sent",
                    "module": "som_polissa_soci",
                    "xml_id": "nou_soci_mail_webforms",
                    "model": "somenergia.soci",
                    "record_id": member_ids[0],
                    "recipient": False,
                    "from_email": False,
                })
        return notifications

    def _send_mail(
        self,
        cursor,
        uid,
        module,
        xml_id,
        src_model,
        record_id,
        recipient,
        from_email=False,
        context=None,
    ):
        imd_obj = self.pool.get("ir.model.data")
        template_id = imd_obj.get_object_reference(cursor, uid, module, xml_id)[1]
        template = self.pool.get("poweremail.templates").read(
            cursor, uid, template_id, ["enforce_from_account"], context=context
        )
        from_id = template.get("enforce_from_account", False)
        if from_email:
            from_ids = self.pool.get("poweremail.core_accounts").search(
                cursor, uid, [("email_id", "=", from_email)], limit=1, context=context
            )
            from_id = from_ids and from_ids[0] or False
        elif from_id:
            from_id = from_id[0]
        if not from_id:
            raise osv.except_osv(
                _("Missing sender account"), _("No sender account is configured."))
        mail_context = {
            "active_ids": [record_id],
            "active_id": record_id,
            "template_id": template_id,
            "src_model": src_model,
            "src_rec_ids": [record_id],
            "from": from_id,
            "state": "single",
            "priority": "2",
        }
        wizard_id = self.pool.get("poweremail.send.wizard").create(
            cursor,
            uid,
            {"state": "single", "priority": "2", "from": from_id, "to": recipient},
            context=mail_context,
        )
        return self.pool.get("poweremail.send.wizard").send_mail(
            cursor, uid, [wizard_id], context=mail_context
        )

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

    def _needs_new_contract(self, cursor, uid, request, context=None):
        return request.owner_change_type == "T"

    def _payment_method(self, request):
        return request.payload.get("payment_method", "bank")

    def _one_id(self, ids):
        if isinstance(ids, (list, tuple)):
            if len(ids) != 1:
                raise osv.except_osv(_("Invalid holder change"),
                                     _("Exactly one request is required."))
            return ids[0]
        return ids

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
        "new_member_partner_id": fields.many2one(
            "res.partner", "New member", readonly=True
        ),
        "owner_notification_sent": fields.boolean("Owner notification sent", readonly=True),
        "old_owner_notification_sent": fields.boolean("Payer notification sent", readonly=True),
        "member_notification_sent": fields.boolean("Member notification sent", readonly=True),
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
