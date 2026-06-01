# -*- coding: utf-8 -*-
from osv import osv, fields


class SomLastMonthAveragePrice(osv.osv):
    _name = "som.last.month.average.price"
    _description = "Previous month prices for simulations"

    _columns = {
        "p1_price": fields.float("P1 average (€/kWh)", required=True),
        "p2_price": fields.float("P2 average (€/kWh)", required=True),
        "p3_price": fields.float("P3 average (€/kWh)", required=True),
        "p4_price": fields.float("P4 average (€/kWh)", required=True),
        "p5_price": fields.float("P5 average (€/kWh)", required=True),
        "p6_price": fields.float("P6 average (€/kWh)", required=True),
        "date": fields.date("Date of prices"),
        "tariff": fields.char("Access tariff", size=64, required=True),
        "type": fields.char("Price type", size=64, required=True),
    }

    def get_current_price(self, cursor, uid, tariff, type, context=None):
        ids = self.search(cursor, uid, [("tariff", "=", tariff),
                          ("type", "=", type)], limit=1,
                          order="date desc, id desc", context=context)
        if not ids:
            return False
        return self.read(
            cursor,
            uid,
            ids[0],
            ["p1_price", "p2_price", "p3_price", "p4_price",
                "p5_price", "p6_price", "date", "tariff", "type"],
            context=context,
        )


SomLastMonthAveragePrice()
