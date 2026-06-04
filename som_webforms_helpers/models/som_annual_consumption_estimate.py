# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv, fields


class SomAnnualConsumptionEstimate(osv.osv):
    _name = "som.annual.consumption.estimate"
    _description = "Annual consumption estimate by power"
    _order = "power asc"

    _columns = {
        "power": fields.integer("Power", required=True),
        "consumption": fields.integer("Estimate Consumption", required=True),
    }

    _sql_constraints = [
        (
            "som_annual_consumption_estimate",
            "unique(power)",
            "Power value must be unique",
        )
    ]

    def _id_power_inferior_o_igual(self, items, value):
        candidates = [d for d in items if d["power"] <= value]
        if not candidates:
            return None
        best = max(candidates, key=lambda d: d["power"])
        return best["id"]

    def get_consumption_by_power(self, cursor, uid, power, context=None):
        all_ids = self.search(cursor, uid, [], context=context)
        id_power_dict = self.read(
            cursor,
            uid,
            all_ids,
            ["power"],
            context=context,
        )

        estimate_id = self._id_power_inferior_o_igual(id_power_dict, power)

        if not estimate_id:
            return False
        estimate = self.read(
            cursor,
            uid,
            estimate_id,
            ["consumption"],
            context=context,
        )
        return estimate["consumption"]


SomAnnualConsumptionEstimate()
