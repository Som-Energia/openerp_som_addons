# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re
from copy import deepcopy

from osv import osv
from tools.translate import _


CUPS_RE = re.compile(r"^ES[0-9]{16}[A-Z]{2}(?:[0-9][A-Z])?$")
LEGAL_PERSON_PREFIXES = set("ABCDEFGHJNPQRSUVW")


class SomHolderChangeWww(osv.osv_memory):
    _name = "som.holder.change.www"
    _description = "Holder change web facade"

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

        if not payload.get("privacy_policy_accepted") \
                or not payload.get("terms_accepted") \
                or not payload["payment"].get("sepa_accepted"):
            return self._error(
                "CONSENT_REQUIRED",
                _("Privacy, contractual and SEPA consent are required."),
            )

        required = {
            "payment": ["iban", "sepa_accepted", "voluntary_cent"],
            "supply_point": ["cups", "address"],
            "member": ["invite_token", "become_member", "link_member"],
            "especial_cases": ["reason_death", "reason_merge", "reason_electrodep"],
            "holder": [
                "name", "vat", "address", "postal_code", "state", "city",
                "email", "phone1", "language",
            ],
        }
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
        request_id = request_obj.create(
            cursor,
            uid,
            {
                "polissa_id": polissa_id,
                "cups": cups,
                "owner_change_type": self._owner_change_type(payload),
                "payload": deepcopy(payload),
            },
            context=context,
        )

        request = request_obj.read(
            cursor, uid, request_id, ["state"], context=context
        )
        return {
            "success": True,
            "request_id": request_id,
            "state": request["state"],
            "signature_url": False,
        }


SomHolderChangeWww()
