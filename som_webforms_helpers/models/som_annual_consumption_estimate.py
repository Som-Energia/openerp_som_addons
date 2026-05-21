# -*- coding: utf-8 -*-
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

    def _id_power_inferior_o_igual(items, value):
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

        ids = self._id_power_inferior_o_igual(self, cursor, uid, id_power_dict, power, context)

        if not ids:
            return False
        return self.read(
            cursor,
            uid,
            ids[0],
            ["consumption"],
            context=context,
        )


SomAnnualConsumptionEstimate()
