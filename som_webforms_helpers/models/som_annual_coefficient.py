# -*- coding: utf-8 -*-
from osv import osv, fields


class SomAnnualCoefficient(osv.osv):
    _name = "som.annual.coefficient"
    _description = "Annual kWh coefficients for simulations"

    _columns = {
        "p1_ratio": fields.float("P1 ratio", required=True),
        "p2_ratio": fields.float("P2 ratio", required=True),
        "p3_ratio": fields.float("P3 ratio", required=True),
        "p4_ratio": fields.float("P4 ratio", required=True),
        "p5_ratio": fields.float("P5 ratio", required=True),
        "p6_ratio": fields.float("P6 ratio", required=True),
        "year": fields.integer("Year of coefficients", required=True),
        "tariff": fields.char("Access tariff", size=64, required=True),
    }

    def get_current_coefficient(self, cursor, uid, tariff, context=None):
        ids = self.search(cursor, uid, [("tariff", "=", tariff)],
                          limit=1, order="year desc", context=context)
        if not ids:
            return False
        return self.read(
            cursor,
            uid,
            ids[0],
            ["p1_ratio", "p2_ratio", "p3_ratio", "p4_ratio",
             "p5_ratio", "p6_ratio", "year", "tariff"],
            context=context,
        )


SomAnnualCoefficient()
