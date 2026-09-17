# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from tools.translate import _


LEGAL_PERSON_PREFIXES = set("ABCDEFGHJNPQRSUVW")
SPECIAL_CASE_ATTACHMENTS = (
    ("reason_death", "death", "holder_change_death"),
    ("reason_merge", "merge", "holder_change_merge"),
    ("reason_electrodep", "medical", "holder_change_medical"),
)


def validate_payload(payload):
    for validator in (
        validate_base_payload,
        validate_required_fields,
        validate_holder,
        validate_member,
        validate_special_case,
    ):
        validation_error = validator(payload)
        if validation_error:
            return validation_error
    return False


def validate_base_payload(payload):
    if not isinstance(payload, dict):
        return error("INVALID_PAYLOAD", _("The payload must be an object."))

    sections = ["payment", "supply_point", "member", "especial_cases", "holder"]
    missing = missing_fields(payload, sections)
    if missing:
        return error(
            "MISSING_REQUIRED_FIELDS",
            _("Missing required fields: {}.").format(", ".join(missing)),
        )

    if not payload.get("privacy_policy_accepted") or not payload.get("terms_accepted"):
        return error(
            "CONSENT_REQUIRED",
            _("Privacy and contractual consent are required."),
        )

    payment_method = payload.get("payment_method")
    if payment_method not in ("bank", "card"):
        return error("INVALID_PAYMENT_METHOD", _("Payment method must be bank or card."))
    if payment_method == "bank" and not payload["payment"].get("sepa_accepted"):
        return error("CONSENT_REQUIRED", _("SEPA consent is required for bank payment."))
    return False


def validate_required_fields(payload):
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
    if payload["payment_method"] == "bank":
        required["payment"].extend(["iban", "sepa_accepted"])
    for section, fields_to_check in required.items():
        missing = missing_fields(payload[section], fields_to_check)
        if missing:
            return error(
                "MISSING_REQUIRED_FIELDS",
                _("Missing {} fields: {}.").format(section, ", ".join(missing)),
            )
    return False


def validate_holder(payload):
    holder = payload["holder"]
    vat = normalize_vat(holder.get("vat"))
    if not vat:
        return error("INVALID_VAT", _("The holder VAT is invalid."))
    person_fields = ["proxyname", "proxynif"] if vat[0] in LEGAL_PERSON_PREFIXES else ["surname1"]
    missing = missing_fields(holder, person_fields)
    if missing:
        return error(
            "MISSING_REQUIRED_FIELDS",
            _("Missing holder fields: {}.").format(", ".join(missing)),
        )
    return False


def validate_member(payload):
    member = payload["member"]
    if member.get("become_member") and member.get("link_member"):
        return error(
            "INVALID_MEMBER_SELECTION",
            _("The holder cannot become a member and link another member."),
        )
    if member.get("link_member"):
        missing = missing_fields(member, ["vat", "number"])
        if missing:
            return error(
                "MISSING_REQUIRED_FIELDS",
                _("Missing member fields: {}.").format(", ".join(missing)),
            )
    return False


def validate_special_case(payload):
    cases = payload["especial_cases"]
    required_attachment = False
    attachment_category = False
    for reason, attachment_name, category in SPECIAL_CASE_ATTACHMENTS:
        if cases.get(reason):
            required_attachment = attachment_name
            attachment_category = category
            break
    attachments = cases.get("attachments", {})
    special_attachments = payload.get("attachments", [])
    has_attachment = not required_attachment or attachments.get(required_attachment) or any(
        attachment.get("category") == attachment_category
        for attachment in special_attachments
    )
    if required_attachment and not has_attachment:
        return error(
            "MISSING_REQUIRED_FIELDS",
            _("The {} attachment is required.").format(required_attachment),
        )
    if required_attachment and special_attachments and any(
        attachment.get("category") != attachment_category
        for attachment in special_attachments
    ):
        return error(
            "INVALID_ATTACHMENT_CATEGORY",
            _("The attachment category does not match the special case."),
        )
    return False


def missing_fields(values, fields_to_check):
    return [field for field in fields_to_check if field not in values]


def normalize_vat(vat):
    vat = (vat or "").replace(" ", "").upper()
    return vat[2:] if vat.startswith("ES") else vat


def error(code, message):
    return {"success": False, "code": code, "error": message}
