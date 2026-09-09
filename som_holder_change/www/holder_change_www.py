# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re
import time
from copy import deepcopy

from osv import osv
from oorq.decorators import job
from service.security import Sudo
from tools.translate import _


CUPS_RE = re.compile(r"^ES[0-9]{16}[A-Z]{2}(?:[0-9][A-Z])?$")
LEGAL_PERSON_PREFIXES = set("ABCDEFGHJNPQRSUVW")


class SomHolderChangeWww(osv.osv_memory):
    _name = "som.holder.change.www"
    _description = "Holder change web facade"
    _SIGNATURE_ERROR_STATUSES = ("error", "canceled", "declined", "expired")

    def _error(self, code, message):
        return {"success": False, "code": code, "error": message}

    def _missing_fields(self, values, fields_to_check):
        return [field for field in fields_to_check if field not in values]

    def _validate_payload(self, payload):
        if not isinstance(payload, dict):
            return self._error("INVALID_PAYLOAD", _("The payload must be an object."))

        sections = ["payment", "supply_point", "member", "especial_cases", "holder"]
        missing = self._missing_fields(payload, sections)
        if missing:
            return self._error(
                "MISSING_REQUIRED_FIELDS",
                _("Missing required fields: {}.").format(", ".join(missing)),
            )

        if not payload.get("privacy_policy_accepted") or not payload.get("terms_accepted"):
            return self._error(
                "CONSENT_REQUIRED",
                _("Privacy and contractual consent are required."),
            )

        payment_method = payload.get("payment_method")
        if payment_method not in ("bank", "card"):
            return self._error("INVALID_PAYMENT_METHOD", _("Payment method must be bank or card."))
        if payment_method == "bank" and not payload["payment"].get("sepa_accepted"):
            return self._error("CONSENT_REQUIRED", _("SEPA consent is required for bank payment."))

        required = {
            "supply_point": ["cups", "address"],
            "member": ["invite_token", "become_member", "link_member"],
            "especial_cases": ["reason_death", "reason_merge", "reason_electrodep"],
            "holder": [
                "name", "vat", "address", "postal_code", "state", "city",
                "email", "phone1", "language",
            ],
        }
        required["payment"] = ["voluntary_cent"]
        if payment_method == "bank":
            required["payment"].extend(["iban", "sepa_accepted"])
        for section, fields_to_check in required.items():
            missing = self._missing_fields(payload[section], fields_to_check)
            if missing:
                return self._error(
                    "MISSING_REQUIRED_FIELDS",
                    _("Missing {} fields: {}.").format(section, ", ".join(missing)),
                )

        holder = payload["holder"]
        vat = self._normalize_vat(holder.get("vat"))
        if not vat:
            return self._error("INVALID_VAT", _("The holder VAT is invalid."))
        is_legal_person = vat[0] in LEGAL_PERSON_PREFIXES
        person_fields = ["proxyname", "proxynif"] if is_legal_person else ["surname1"]
        missing = self._missing_fields(holder, person_fields)
        if missing:
            return self._error(
                "MISSING_REQUIRED_FIELDS",
                _("Missing holder fields: {}.").format(", ".join(missing)),
            )

        member = payload["member"]
        if member.get("become_member") and member.get("link_member"):
            return self._error(
                "INVALID_MEMBER_SELECTION",
                _("The holder cannot become a member and link another member."),
            )
        if member.get("link_member"):
            missing = self._missing_fields(member, ["vat", "number"])
            if missing:
                return self._error(
                    "MISSING_REQUIRED_FIELDS",
                    _("Missing member fields: {}.").format(", ".join(missing)),
                )

        cases = payload["especial_cases"]
        attachments = cases.get("attachments", {})
        required_attachment = False
        if cases.get("reason_death"):
            required_attachment = "death"
        elif cases.get("reason_merge"):
            required_attachment = "merge"
        elif cases.get("reason_electrodep"):
            required_attachment = "medical"
        if required_attachment and not attachments.get(required_attachment):
            return self._error(
                "MISSING_REQUIRED_FIELDS",
                _("The {} attachment is required.").format(required_attachment),
            )
        return False

    def _normalize_cups(self, cups):
        return (cups or "").replace(" ", "").upper()

    def _normalize_vat(self, vat):
        vat = (vat or "").replace(" ", "").upper()
        return vat[2:] if vat.startswith("ES") else vat

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

    def _owner_change_type(self, payload):
        cases = payload["especial_cases"]
        special_case = any([
            cases.get("reason_death"),
            cases.get("reason_merge"),
            cases.get("reason_electrodep"),
        ])
        return "S" if special_case else "T"

    def _get_request(self, cursor, uid, request_id, cups, context=None):
        request = self.pool.get("som.holder.change.request").browse(
            cursor, uid, request_id, context=context
        )
        if self._normalize_cups(cups) != request.cups:
            raise osv.except_osv(_("Invalid holder change"), _(
                "The request does not match this CUPS."))
        return request

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

    def create_request(self, cursor, uid, payload, context=None):
        if context is None:
            context = {}
        validation_error = self._validate_payload(payload)
        if validation_error:
            return validation_error
        cups = self._normalize_cups(payload["supply_point"]["cups"])
        if not CUPS_RE.match(cups):
            return self._error("INVALID_CUPS", _("The CUPS format is invalid."))
        polissa_id, contract_error = self._find_contract(
            cursor, uid, cups, context=context
        )
        if contract_error:
            return self._error(contract_error, _("The contract is not available."))

        polissa = self.pool.get("giscedata.polissa").browse(
            cursor, uid, polissa_id, context=context
        )
        current_vat = self._normalize_vat(polissa.titular.vat)
        new_vat = self._normalize_vat(payload["holder"]["vat"])
        if current_vat == new_vat:
            return self._error(
                "SAME_OWNER", _("The new holder must differ from the current holder.")
            )

        request_obj = self.pool.get("som.holder.change.request")
        stored_payload = deepcopy(payload)
        attachments = stored_payload.pop("attachments", [])
        for attachment in attachments:
            attachment.pop("datas", None)
        request_id = request_obj.create(
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
            return self._error("SIMULATION_ERROR", str(error))

        request = request_obj.read(
            cursor, uid, request_id, ["state"], context=context
        )
        return {
            "success": True,
            "request_id": request_id,
            "state": request["state"],
            "signature_url": False,
        }

    def add_payment_card_data(self, cursor, uid, request_id, card_values, context=None):
        request_obj = self.pool.get("som.holder.change.request")
        request = request_obj.browse(cursor, uid, request_id, context=context)
        cursor.commit()
        request_obj.set_card_data(cursor, uid, request_id, card_values, context=context)
        return {"success": True, "request_id": request.id, "state": "awaiting_signature"}

    def sign_request(self, cursor, uid, request_id, cups, context=None):
        if context is None:
            context = {}
        request = self._get_request(cursor, uid, request_id, cups, context=context)
        if request.signature_process_id:
            return {"url": request.signature_process_id.signature_url}
        if request.state != "awaiting_signature":
            raise osv.except_osv(_("Invalid request state"), _(
                "The request is not ready for signing."))

        holder = request.payload["holder"]
        files = [(0, 0, {"doc_file": request.contract_pdf,
                  "filename": "contract-with-summary.pdf"})]
        if request.mandate_pdf:
            files.append((0, 0, {"doc_file": request.mandate_pdf,
                         "filename": "bank-authorization.pdf"}))
        process_obj = self.pool.get("giscedata.signatura.process")
        values = {
            "delivery_type": "url",
            "provider": "signaturit",
            "lang": holder["language"],
            "data": "{}",
            "all_signed": True,
            "recipients": [(0, 0, {"name": holder["name"], "email": holder["email"]})],
            "files": files,
        }
        cursor.commit()
        with Sudo(uid=uid, gid=0):
            process_id = process_obj.create(cursor, uid, values, context=context)
            process_obj.start(cursor, uid, [process_id], context=context)
        request_obj = self.pool.get("som.holder.change.request")
        request_obj.write(cursor, uid, [request_id], {
                          "signature_process_id": process_id}, context=context)

        deadline = time.time() + 200.0
        signature_url = False
        while time.time() < deadline:
            process = process_obj.read(cursor, uid, process_id, [
                                       "signature_url", "status"], context=context)
            signature_url = process["signature_url"]
            if signature_url:
                break
            if process["status"] in self._SIGNATURE_ERROR_STATUSES:
                raise osv.except_osv(_("Signature error"), _("The signature process failed."))
            time.sleep(0.2)
        if not signature_url:
            raise osv.except_osv(_("Signature error"), _(
                "Timed out waiting for the signature URL."))
        lang = holder["language"].split("_")[0]
        signature_url = signature_url.replace(
            "app.", "sign-app.").replace("document", "v1/{}".format(lang))
        return {"url": signature_url}

    def execute_request(self, cursor, uid, request_id, cups, context=None):
        if context is None:
            context = {}
        request = self._get_request(cursor, uid, request_id, cups, context=context)
        if not request.signature_process_id:
            raise osv.except_osv(_("Signature required"), _(
                "The request has not been sent for signing."))
        process_obj = self.pool.get("giscedata.signatura.process")
        process_obj.update(cursor, uid, [request.signature_process_id.id], context=context)
        status = process_obj.read(cursor, uid, request.signature_process_id.id, [
                                  "status"], context=context)["status"]
        if status != "completed":
            raise osv.except_osv(_("Signature required"), _(
                "The signature has not been completed."))
        request_obj = self.pool.get("som.holder.change.request")
        request_obj.write(cursor, uid, [request_id], {"state": "queued"}, context=context)
        self.execute_request_async(cursor, uid, request_id, context=context)
        return {"success": True, "request_id": request_id, "state": "queued"}

    @job(queue="leads", timeout=300)
    def execute_request_async(self, cursor, uid, request_id, context=None):
        request_obj = self.pool.get("som.holder.change.request")
        try:
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


SomHolderChangeWww()
