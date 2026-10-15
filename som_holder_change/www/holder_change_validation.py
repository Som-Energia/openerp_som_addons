# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from tools.translate import _


LEGAL_PERSON_PREFIXES = set("ABCDEFGHJNPQRSUVW")
LINKED_MEMBER_TYPES = ("new_member", "sponsored", "without_member")
PAYMENT_TYPES = ("remesa", "tpv")
SPECIAL_CASE_ATTACHMENTS = (
    ("reason_death", "death", "holder_change_death"),
    ("reason_merge", "merge", "holder_change_merge"),
    ("reason_electrodep", "medical", "holder_change_medical"),
)


def validate_payload(payload):
    for validator in (
        validate_base_payload,
        validate_required_fields,
        validate_payment,
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

    sections = ["contract_info", "contract_owner", "especial_cases"]
    missing = missing_fields(payload, sections)
    if missing:
        return error(
            "MISSING_REQUIRED_FIELDS",
            _("Missing required fields: {}.").format(", ".join(missing)),
        )

    if (
        not payload.get("privacy_conditions")
        or not payload.get("general_contract_terms_accepted")
    ):
        return error(
            "CONSENT_REQUIRED",
            _("Privacy and contractual consent are required."),
        )

    payment_type = payload.get("payment_type")
    if payment_type not in PAYMENT_TYPES:
        return error(
            "INVALID_PAYMENT_METHOD",
            _("Payment type must be remesa or tpv."),
        )
    if payment_type == "remesa" and not payload.get("sepa_accepted"):
        return error("CONSENT_REQUIRED", _("SEPA consent is required for bank payment."))
    if payment_type == "tpv" and not payload.get("payment_authorization_accepted"):
        return error(
            "CONSENT_REQUIRED", _("Card payment authorization is required."))
    return False


def validate_required_fields(payload):
    required = {
        "payload": ["linked_member", "donation"],
        "contract_info": ["cups"],
        "especial_cases": ["reason_death", "reason_merge", "reason_electrodep"],
        "contract_owner": [
            "name", "vat", "address", "email", "phone", "lang",
        ],
        "address": ["street", "number", "postal_code", "state_id", "city_id"],
    }
    if payload["payment_type"] == "remesa":
        required["payload"].append("iban")
    for section, fields_to_check in required.items():
        if section == "payload":
            values = payload
        elif section == "address":
            values = payload["contract_owner"].get("address", {})
        else:
            values = payload[section]
        missing = missing_fields(values, fields_to_check)
        if missing:
            return error(
                "MISSING_REQUIRED_FIELDS",
                _("Missing {} fields: {}.").format(section, ", ".join(missing)),
            )
    return False


def validate_payment(payload):
    if not isinstance(payload["donation"], bool):
        return error(
            "INCORRECT_PARAM_TYPE",
            _("Voluntary cent must be a boolean."),
        )
    return False


def validate_holder(payload):
    contract_owner = payload["contract_owner"]
    vat = normalize_vat(contract_owner.get("vat"))
    if not vat:
        return error("INVALID_VAT", _("The holder VAT is invalid."))
    person_fields = (
        ["proxy_name", "proxy_vat"]
        if vat[0] in LEGAL_PERSON_PREFIXES else ["surname"]
    )
    missing = missing_fields(contract_owner, person_fields)
    if missing:
        return error(
            "MISSING_REQUIRED_FIELDS",
            _("Missing holder fields: {}.").format(", ".join(missing)),
        )
    return False


def validate_member(payload):
    linked_member = payload["linked_member"]
    if linked_member not in LINKED_MEMBER_TYPES:
        return error(
            "INVALID_MEMBER_SELECTION",
            _("The linked member selection is invalid."),
        )
    if linked_member == "sponsored":
        member = payload.get("linked_member_info", {})
        missing = missing_fields(member, ["vat", "code"])
        if missing:
            return error(
                "MISSING_REQUIRED_FIELDS",
                _("Missing member fields: {}.").format(", ".join(missing)),
            )
    return False


def validate_special_case(payload):
    cases = payload["especial_cases"]
    reasons = [reason for reason, _name, _category in SPECIAL_CASE_ATTACHMENTS]
    if any(not isinstance(cases[reason], bool) for reason in reasons):
        return error(
            "INCORRECT_PARAM_TYPE",
            _("Special case reasons must be booleans."),
        )
    active_reasons = [reason for reason in reasons if cases[reason]]
    if len(active_reasons) > 1:
        return error(
            "INVALID_SPECIAL_CASE",
            _("Only one special case reason can be selected."),
        )
    required_attachment = False
    attachment_category = False
    for reason, attachment_name, category in SPECIAL_CASE_ATTACHMENTS:
        if cases.get(reason):
            required_attachment = attachment_name
            attachment_category = category
            break
    special_attachments = payload.get("attachments", [])
    special_categories = set(
        category for _reason, _name, category in SPECIAL_CASE_ATTACHMENTS
    )
    if not required_attachment and any(
        attachment.get("category") in special_categories
        for attachment in special_attachments
    ):
        return error(
            "INVALID_ATTACHMENT_CATEGORY",
            _("A special attachment requires its corresponding special case."),
        )
    if required_attachment and special_attachments and any(
        attachment.get("category") != attachment_category
        for attachment in special_attachments
    ):
        return error(
            "INVALID_ATTACHMENT_CATEGORY",
            _("The attachment category does not match the special case."),
        )
    has_attachment = not required_attachment or any(
        attachment.get("category") == attachment_category
        for attachment in special_attachments
    )
    if required_attachment and not has_attachment:
        return error(
            "MISSING_REQUIRED_FIELDS",
            _("The {} attachment is required.").format(required_attachment),
        )
    return False


def missing_fields(values, fields_to_check):
    return [field for field in fields_to_check if field not in values]


def normalize_vat(vat):
    vat = (vat or "").replace(" ", "").upper()
    return vat[2:] if vat.startswith("ES") else vat


def error(code, message):
    return {"success": False, "code": code, "error": message}
