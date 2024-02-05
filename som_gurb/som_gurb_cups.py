# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import logging
from datetime import datetime

logger = logging.getLogger("openerp.{}".format(__name__))


class SomGurbCups(osv.osv):
    _name = "som.gurb.cups"
    _description = _("CUPS en grup de generació urbana")

    def _ff_get_beta_percentage(self, cursor, uid, ids, field_name, arg, context=None):
        gurb_obj = self.pool.get("som.gurb")
        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, ["gurb_id", "beta_kw"]):
            gurb_id = gurb_cups_vals.get("gurb_id", False)
            if gurb_id:
                generation_power = gurb_obj.read(
                    cursor, uid, gurb_id[0], ["generation_power"]
                )["generation_power"]

                if generation_power:
                    beta_kw = gurb_cups_vals.get("beta_kw", 0)
                    res[gurb_cups_vals["id"]] = beta_kw * 100 / generation_power
                else:
                    res[gurb_cups_vals["id"]] = 0
        return res

    # TODO: pensar
    def _ff_is_model_active(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, False)
        for cups_gurb_id in ids:
            end_date = self.read(cursor, uid, cups_gurb_id, ["end_date"])["end_date"]
            if end_date:
                end_date_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                today_time = datetime.strptime(datetime.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
                if today_time > end_date_datetime:
                    res[cups_gurb_id] = False
                else:
                    res[cups_gurb_id] = True
            else:
                res[cups_gurb_id] = True
        return res

    _columns = {
        "active": fields.boolean("Actiu"),
        "start_date": fields.date(u"Data entrada GURB", required=True),
        "end_date": fields.date(u"Data sortida GURB",),
        "gurb_id": fields.many2one("som.gurb", "GURB", required=True),
        "cups_id": fields.many2one("giscedata.cups.ps", "CUPS", required=True),
        "beta_kw": fields.float(
            "Beta (kW)",
            digits=(10, 3),
            required=True,
        ),
        "beta_percentage": fields.function(
            _ff_get_beta_percentage,
            type="float",
            string="Beta (%)",
            digits=(12, 4),
            method=True,
        )
    }

    _defaults = {
        "active": lambda *a: True,
    }


SomGurbCups()
