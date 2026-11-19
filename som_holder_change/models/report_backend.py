# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from osv import osv

from .holder_change_reports import CARD_PLACEHOLDER_CONTEXT


class HolderChangeContractSummary(osv.osv):
    _name = "report.backend.contract.summary"
    _inherit = "report.backend.contract.summary"

    def get_payment_data(self, cursor, uid, pol, context=None):
        result = super(HolderChangeContractSummary, self).get_payment_data(
            cursor, uid, pol, context=context
        )
        placeholder = (context or {}).get(CARD_PLACEHOLDER_CONTEXT)
        if placeholder and result["is_card"]:
            result.update({"last4": placeholder, "label": "**** **** **** {}".format(placeholder)})
        return result


HolderChangeContractSummary()


class HolderChangeContractConditions(osv.osv):
    _name = "report.backend.condicions.particulars"
    _inherit = "report.backend.condicions.particulars"

    def get_titular_data(self, cursor, uid, pol, pas01, context=None):
        result = super(HolderChangeContractConditions, self).get_titular_data(
            cursor, uid, pol, pas01, context=context
        )
        placeholder = (context or {}).get(CARD_PLACEHOLDER_CONTEXT)
        if placeholder and result["is_recurrent_card_payment"]:
            result["printable_card_number"] = placeholder
        return result


HolderChangeContractConditions()
