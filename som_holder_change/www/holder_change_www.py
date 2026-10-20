# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re
import time
from copy import deepcopy

import pooler

from osv import osv
from oorq.decorators import job
from service.security import Sudo
from tools.translate import _

from . import holder_change_validation

CUPS_RE = re.compile(r"^ES[0-9]{16}[A-Z]{2}(?:[0-9][A-Z])?$")
ACTIVE_REQUEST_STATES = (
    "received", "awaiting_payment", "awaiting_signature", "queued",
)


class SomHolderChangeWww(osv.osv_memory):
    _name = "som.holder.change.www"
    _description = "Holder change web facade"
    _SIGNATURE_ERROR_STATUSES = ("error", "canceled", "declined", "expired")
    _SIGNATURE_RETRY_ATTEMPTS = 5
    _SIGNATURE_RETRY_WAIT_SECONDS = 10

    def create_request(self, cursor, uid, payload, context=None):
        if context is None:
            context = {}
        validation_error = holder_change_validation.validate_payload(payload)
        if validation_error:
            return validation_error

        cups = self._normalize_cups(payload["contract_info"]["cups"])
        if not CUPS_RE.match(cups):
            return holder_change_validation.error("INVALID_CUPS", _("The CUPS format is invalid."))

        polissa_id, contract_error = self._find_contract(cursor, uid, cups, context=context)
        if contract_error:
            return holder_change_validation.error(
                contract_error, _("The contract is not available."))

        if self._is_inactive_holder(
            cursor, uid, payload["contract_owner"]["vat"], context=context
        ):
            return holder_change_validation.error(
                "CUSTOMER_INACTIVE", _("The new holder is inactive."))

        modifiable_error = self._check_contract_modifiable(cursor, uid, polissa_id, context=context)
        if modifiable_error:
            return modifiable_error

        polissa = self.pool.get("giscedata.polissa").browse(
            cursor, uid, polissa_id, context=context)
        current_vat = self._normalize_vat(polissa.titular.vat)
        new_vat = self._normalize_vat(payload["contract_owner"]["vat"])
        if current_vat == new_vat:
            return holder_change_validation.error(
                "SAME_OWNER", _("The new holder must differ from the current holder.")
            )

        # Serializing on the contract prevents concurrent requests for one CUPS.
        cursor.execute(
            "SELECT id FROM giscedata_polissa WHERE id = %s FOR UPDATE",
            (polissa_id,),
        )
        if self._active_request_for_contract(cursor, uid, polissa_id, context=context):
            return holder_change_validation.error(
                "REQUEST_IN_PROGRESS",
                _("There is already an active holder change request for this CUPS."),
            )

        request_id = self._store_request(
            cursor, uid, payload, cups, polissa_id, context=context)

        preparation_error = self._prepare_stored_request(
            cursor, uid, request_id, context=context)

        return preparation_error or self._request_response(
            cursor, uid, request_id, context=context)

    def add_payment_card_data(
        self, cursor, uid, request_id, cups, card_values, context=None
    ):
        request_obj = self.pool.get("som.holder.change.request")
        request = self._get_request(cursor, uid, request_id, cups, context=context)
        cursor.commit()
        request_obj.set_card_data(cursor, uid, request_id, card_values, context=context)
        return {"success": True, "request_id": request.id, "state": "awaiting_signature"}

    def sign_request(self, cursor, uid, request_id, cups, context=None):
        if context is None:
            context = {}
        request = self._get_request(cursor, uid, request_id, cups, context=context)
        process_obj = self.pool.get("giscedata.signatura.process")
        request_obj = self.pool.get("som.holder.change.request")
        if request.signature_process_id and request.signature_process_id.signature_url:
            return {"url": self._localized_signature_url(
                request.signature_process_id.signature_url,
                request.payload["contract_owner"]["lang"],
            )}
        if request.signature_process_id:
            process_id = request.signature_process_id.id
        elif request.state != "awaiting_signature":
            raise osv.except_osv(_("Invalid request state"), _(
                "The request is not ready for signing."))
        else:
            cursor.commit()
            # Keep the provider process associated even if URL polling later fails.
            with pooler.get_db(cursor.dbname).cursor() as registration_cursor:
                with Sudo(uid=uid, gid=0):
                    process_id = process_obj.create(
                        registration_cursor,
                        uid,
                        self._signature_process_values(registration_cursor, uid, request),
                        context=context,
                    )
                    request_obj.write(
                        registration_cursor,
                        uid,
                        [request_id],
                        {"signature_process_id": process_id},
                        context=context,
                    )
                    registration_cursor.commit()

        # start() is idempotent once the provider signature ID is stored.
        start_error = None
        with pooler.get_db(cursor.dbname).cursor() as signature_cursor:
            with Sudo(uid=uid, gid=0):
                try:
                    process_obj.start(
                        signature_cursor, uid, [process_id], context=context
                    )
                except Exception as error:
                    start_error = error
                signature_cursor.commit()

        if start_error:
            raise start_error

        signature_url = self._wait_for_signature_url(
            cursor, uid, process_obj, process_id, context=context
        )
        return {"url": self._localized_signature_url(
            signature_url, request.payload["contract_owner"]["lang"]
        )}

    @job(queue="leads", timeout=300)
    def execute_request_async(self, cursor, uid, request_id, context=None):
        request_obj = self.pool.get("som.holder.change.request")
        try:
            signature_result = self._signature_allows_execution(
                cursor, uid, request_id, context=context
            )
        except Exception as error:
            request_obj.write(
                cursor, uid, [request_id],
                {"state": "awaiting_signature", "error_code": "SIGNATURE_ERROR",
                 "error_message": str(error)},
                context=context,
            )
            raise

        if not signature_result["completed"]:
            self._return_to_signature_wait(
                cursor, uid, request_id, signature_result, context=context
            )
            return signature_result

        try:
            request_obj.write(
                cursor, uid, [request_id],
                {"error_code": False, "error_message": False}, context=context,
            )
            return request_obj.execute(cursor, uid, request_id, context=context)
        except Exception as error:
            request_obj.write(
                cursor,
                uid,
                [request_id],
                {"state": "execution_error", "error_code": "EXECUTION_ERROR",
                    "error_message": str(error)},
                context=context,
            )
            raise

    def _return_to_signature_wait(self, cursor, uid, request_id, result, context=None):
        self.pool.get("som.holder.change.request").write(
            cursor, uid, [request_id],
            {"state": "awaiting_signature", "error_code": result["code"],
             "error_message": result["message"]},
            context=context,
        )

    def execute_request(self, cursor, uid, request_id, cups, context=None):
        if context is None:
            context = {}

        request = self._get_request(cursor, uid, request_id, cups, context=context)
        if not request.signature_process_id:
            raise osv.except_osv(_("Signature required"), _(
                "The request has not been sent for signing."))

        request_obj = self.pool.get("som.holder.change.request")
        cursor.execute(
            "SELECT id FROM som_holder_change_request WHERE id = %s FOR UPDATE",
            (request_id,),
        )
        request = self._get_request(cursor, uid, request_id, cups, context=context)
        if request.state == "queued":
            return {"success": True, "request_id": request_id, "state": "queued"}
        if request.state == "completed":
            return {"success": True, "request_id": request_id, "state": "completed"}
        if request.state != "awaiting_signature":
            raise osv.except_osv(_("Invalid request state"), _(
                "The request is not ready for execution."))

        request_obj.write(
            cursor, uid, [request_id],
            {"state": "queued", "error_code": False, "error_message": False},
            context=context,
        )
        cursor.commit()
        try:
            self.execute_request_async(cursor, uid, request_id, context=context)
        except Exception as error:
            self._restore_request_after_enqueue_failure(
                cursor, uid, request_id, error, context=context
            )
            raise
        return {"success": True, "request_id": request_id, "state": "queued"}

    def _restore_request_after_enqueue_failure(
        self, cursor, uid, request_id, error, context=None
    ):
        request_obj = self.pool.get("som.holder.change.request")
        with pooler.get_db(cursor.dbname).cursor() as recovery_cursor:
            recovery_cursor.execute(
                "SELECT id FROM som_holder_change_request WHERE id = %s FOR UPDATE",
                (request_id,),
            )
            request = request_obj.browse(
                recovery_cursor, uid, request_id, context=context
            )
            # A job may have started despite an enqueue-side error. Never undo
            # a state transition that the worker has already advanced.
            if request.state == "queued":
                request_obj.write(
                    recovery_cursor, uid, [request_id],
                    {"state": "awaiting_signature", "error_code": "QUEUE_ERROR",
                     "error_message": str(error)},
                    context=context,
                )
                recovery_cursor.commit()

    def _signature_allows_execution(self, cursor, uid, request_id, context=None):
        if context is None:
            context = {}
        request_obj = self.pool.get("som.holder.change.request")
        process_obj = self.pool.get("giscedata.signatura.process")
        attempts = context.get("signature_attempts", self._SIGNATURE_RETRY_ATTEMPTS)
        wait_seconds = context.get(
            "signature_retry_wait_seconds", self._SIGNATURE_RETRY_WAIT_SECONDS
        )
        db = pooler.get_db(cursor.dbname)

        for attempt in range(attempts):
            tmp_cursor = db.cursor()
            try:
                request = request_obj.browse(
                    tmp_cursor, uid, request_id, context=context
                )
                if not request.signature_process_id:
                    return {
                        "completed": False, "code": "SIGNATURE_REQUIRED",
                        "message": "The request has not been sent for signing.",
                    }
                process_id = request.signature_process_id.id
                status = process_obj.read(
                    tmp_cursor, uid, process_id, ["status"], context=context
                )["status"]
                if status == "completed":
                    return {"completed": True}
                if status in self._SIGNATURE_ERROR_STATUSES or status == "unsend":
                    return {
                        "completed": False, "code": "SIGNATURE_FAILED",
                        "message": "The signature process ended with status {}.".format(status),
                    }
                process_obj.update(tmp_cursor, uid, [process_id], context=context)
                tmp_cursor.commit()
                status = process_obj.read(
                    tmp_cursor, uid, process_id, ["status"], context=context
                )["status"]
                if status == "completed":
                    return {"completed": True}
                if status in self._SIGNATURE_ERROR_STATUSES or status == "unsend":
                    return {
                        "completed": False, "code": "SIGNATURE_FAILED",
                        "message": "The signature process ended with status {}.".format(status),
                    }
            finally:
                tmp_cursor.close()
            if attempt < attempts - 1:
                time.sleep(wait_seconds)

        return {
            "completed": False, "code": "SIGNATURE_PENDING",
            "message": "The signature is still pending. Please retry later.",
        }

    def _find_contract(self, cursor, uid, cups, context=None):
        cups_obj = self.pool.get("giscedata.cups.ps")
        polissa_obj = self.pool.get("giscedata.polissa")
        cups_ids = cups_obj.search(
            cursor,
            uid,
            [("name", "like", "{}%".format(cups[:20]))],
            context=context,
        )
        if not cups_ids:
            return False, "CUPS_NOT_FOUND"
        contract_ids = polissa_obj.search(
            cursor,
            uid,
            [("cups", "in", cups_ids), ("state", "=", "activa")],
            limit=1,
            context=context,
        )
        if not contract_ids:
            return False, "CONTRACT_NOT_ACTIVE"
        return contract_ids[0], False

    def _is_inactive_holder(self, cursor, uid, vat, context=None):
        inactive_context = (context or {}).copy()
        inactive_context["active_test"] = False
        return bool(self.pool.get("res.partner").search(
            cursor,
            uid,
            [("vat", "=", "ES{}".format(self._normalize_vat(vat))), ("active", "=", False)],
            limit=1,
            context=inactive_context,
        ))

    def _check_contract_modifiable(self, cursor, uid, polissa_id, context=None):
        polissa = self.pool.get("giscedata.polissa").browse(
            cursor, uid, polissa_id, context=context
        )
        if not polissa.modcontractuals_ids:
            return self._check_open_atr(cursor, uid, polissa_id, context=context)
        try:
            self.pool.get("giscedata.polissa").check_modifiable_polissa(
                cursor, uid, polissa_id, context=context
            )
        except Exception as error:
            return holder_change_validation.error("CONTRACT_NOT_MODIFIABLE", str(error))
        return False

    def _check_open_atr(self, cursor, uid, polissa_id, context=None):
        atr_ids = self.pool.get("giscedata.switching").search(
            cursor,
            uid,
            [
                ("cups_polissa_id", "=", polissa_id),
                ("state", "in", ["open", "draft", "pending"]),
                ("proces_id.name", "!=", "R1"),
            ],
            context=context,
        )
        if atr_ids:
            return holder_change_validation.error(
                "CONTRACT_NOT_MODIFIABLE", _("The contract has an open ATR case.")
            )
        return False

    def _get_request(self, cursor, uid, request_id, cups, context=None):
        request = self.pool.get("som.holder.change.request").browse(
            cursor, uid, request_id, context=context
        )
        if self._normalize_cups(cups) != request.cups:
            raise osv.except_osv(_("Invalid holder change"), _(
                "The request does not match this CUPS."))
        return request

    def _active_request_for_contract(self, cursor, uid, polissa_id, context=None):
        request_ids = self.pool.get("som.holder.change.request").search(
            cursor,
            uid,
            [("polissa_id", "=", polissa_id), ("state", "in", ACTIVE_REQUEST_STATES)],
            limit=1,
            context=context,
        )
        return request_ids and request_ids[0] or False

    def _store_request(self, cursor, uid, payload, cups, polissa_id, context=None):
        stored_payload = deepcopy(payload)
        if stored_payload["payment_type"] == "remesa":
            stored_payload["iban"] = "".join(
                char.upper() for char in stored_payload["iban"]
                if char.isalnum()
            )
        attachments = stored_payload.get("attachments", [])
        for attachment in attachments:
            attachment.pop("datas", None)

        request_id = self.pool.get("som.holder.change.request").create(
            cursor,
            uid,
            {
                "polissa_id": polissa_id,
                "cups": cups,
                "owner_change_type": self._owner_change_type(payload),
                "payload": stored_payload,
            },
            context=context,
        )
        self._create_attachments(
            cursor,
            uid,
            request_id,
            payload.get("attachments", []),
            context=context,
        )
        return request_id

    def _create_attachments(self, cursor, uid, request_id, attachments, context=None):
        category_obj = self.pool.get("ir.attachment.category")
        attachment_obj = self.pool.get("ir.attachment")
        for attachment in attachments:
            category_ids = category_obj.search(
                cursor, uid, [("code", "=", attachment["category"])], context=context
            )
            if not category_ids:
                raise osv.except_osv(
                    _("Invalid attachment"),
                    _("Unknown attachment category: {}.").format(attachment["category"]),
                )
            attachment_obj.create(
                cursor,
                uid,
                {
                    "res_model": "som.holder.change.request",
                    "res_id": request_id,
                    "datas_fname": attachment["filename"],
                    "name": attachment["filename"],
                    "category_id": category_ids[0],
                    "datas": attachment["datas"],
                },
                context=context,
            )

    def _prepare_stored_request(self, cursor, uid, request_id, context=None):
        request_obj = self.pool.get("som.holder.change.request")
        # The simulation uses an independent cursor, so it must see the request.
        cursor.commit()
        try:
            request_obj.prepare(cursor, uid, request_id, context=context)
        except Exception as error:
            request_obj.write(
                cursor,
                uid,
                [request_id],
                {"state": "validation_error", "error_code": "SIMULATION_ERROR",
                    "error_message": str(error)},
                context=context,
            )
            return holder_change_validation.error("SIMULATION_ERROR", str(error))
        return None

    def _request_response(self, cursor, uid, request_id, context=None):
        request = self.pool.get("som.holder.change.request").read(
            cursor, uid, request_id, ["state"], context=context
        )
        return {
            "success": True,
            "request_id": request_id,
            "state": request["state"],
            "signature_url": False,
        }

    def _signature_process_values(self, cursor, uid, request):
        template_id = self.pool.get("ir.model.data").get_object_reference(
            cursor,
            uid,
            "som_holder_change",
            "email_signature_process_holder_change",
        )[1]
        contract_owner = request.payload["contract_owner"]
        files = [(0, 0, {"doc_file": request.contract_pdf,
                  "filename": "contract-with-summary.pdf"})]
        if request.mandate_pdf:
            files.append((0, 0, {"doc_file": request.mandate_pdf,
                          "filename": "bank-authorization.pdf"}))
        return {
            "template_id": template_id,
            "template_res_id": request.id,
            "delivery_type": "url",
            "provider": "signaturit",
            "lang": contract_owner["lang"],
            "data": "{}",
            "all_signed": True,
            "recipients": [(0, 0, {
                "name": contract_owner["name"],
                "email": contract_owner["email"],
            })],
            "files": files,
        }

    def _wait_for_signature_url(self, cursor, uid, process_obj, process_id, context=None):
        deadline = time.time() + 200.0
        while time.time() < deadline:
            process = process_obj.read(cursor, uid, process_id, [
                "signature_url", "status"], context=context)
            if process["signature_url"]:
                return process["signature_url"]
            if process["status"] in self._SIGNATURE_ERROR_STATUSES:
                raise osv.except_osv(
                    _("Signature error"), _("The signature process failed."))
            time.sleep(0.2)
        raise osv.except_osv(
            _("Signature error"), _("Timed out waiting for the signature URL."))

    def _localized_signature_url(self, signature_url, language):
        lang = language.split("_")[0]
        return signature_url.replace(
            "app.", "sign-app.").replace("document", "v1/{}".format(lang))

    def _error(self, code, message):
        return {"success": False, "code": code, "error": message}

    def _normalize_cups(self, cups):
        return (cups or "").replace(" ", "").upper()

    def _normalize_vat(self, vat):
        vat = (vat or "").replace(" ", "").upper()
        return vat[2:] if vat.startswith("ES") else vat

    def _owner_change_type(self, payload):
        cases = payload["especial_cases"]
        special_case = any([
            cases.get("reason_death"),
            cases.get("reason_merge"),
            cases.get("reason_electrodep"),
        ])
        return "S" if special_case else "T"


SomHolderChangeWww()
