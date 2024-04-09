# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import logging
from datetime import datetime

logger = logging.getLogger("openerp.{}".format(__name__))


class SomGurbCups(osv.osv):
    _name = "som.gurb.cups"
    _description = _("CUPS en grup de generació urbana")

    def _ff_is_owner(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}

        gurb_obj = self.pool.get("som.gurb")
        pol_obj = self.pool.get("giscedata.polissa")

        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, ["gurb_id"]):
            gurb_vals = gurb_obj.read(cursor, uid, gurb_cups_vals["gurb_id"][0], ["roof_owner_id"])
            cups_id = self.read(cursor, uid, gurb_cups_vals["id"], ["cups_id"])["cups_id"][0]
            search_params = [
                ("state", "=", "activa"),
                ("cups", "=", cups_id),
                ("titular", "=", gurb_vals["roof_owner_id"][0])
            ]

            pol_id = pol_obj.search(cursor, uid, search_params, context=context, limit=1)
            res[gurb_cups_vals["id"]] = bool(pol_id)

        return res

    def _ff_get_beta_percentage(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        gurb_obj = self.pool.get("som.gurb")
        res = dict.fromkeys(ids, False)
        for gurb_cups_vals in self.read(cursor, uid, ids, ["gurb_id", "beta_kw", "extra_beta_kw"]):
            gurb_id = gurb_cups_vals.get("gurb_id", False)
            if gurb_id:
                generation_power = gurb_obj.read(
                    cursor, uid, gurb_id[0], ["generation_power"]
                )["generation_power"]

                if generation_power:
                    beta_kw = gurb_cups_vals.get("beta_kw", 0)
                    extra_beta_kw = gurb_cups_vals.get("extra_beta_kw", 0)
                    res[gurb_cups_vals["id"]] = (extra_beta_kw + beta_kw) * 100 / generation_power
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

    def add_service_to_contract(self, cursor, uid, ids, data_inici, context=None):
        if context is None:
            context = {}

        pol_o = self.pool.get("giscedata.polissa")
        gurb_o = self.pool.get("som.gurb")
        wiz_service_o = self.pool.get("wizard.create.service")
        imd_o = self.openerp.pool.get("ir.model.data")

        owner_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_owner_gurb"
        )[1]

        gurb_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_gurb"
        )[1]

        for gurb_cups_id in ids:
            gurb_vals = self.read(cursor, uid, gurb_cups_id, ["cups_id", "gurb_id", "owner_cups"])
            search_params = [
                ("state", "=", "activa"),
                ("cups", "=", gurb_vals["cups_id"][0]),
            ]

            pol_ids = pol_o.search(cursor, uid, search_params, context=context, limit=1)
            if not pol_ids:
                error_title = _("No hi ha pòlisses actives per aquest CUPS"),
                error_info = _(
                    "El CUPS id {} no té pòlisses actives. No es pot afegir cap servei".format(
                        gurb_vals["cups_id"][0]
                    )
                )
                raise osv.except_osv(error_title, error_info)

            # Get related GURB service pricelist
            pricelist_id = gurb_o.read(
                cursor, uid, gurb_vals["gurb_id"][0], ["pricelist_id"], context=context
            )["pricelist_id"]

            # Afegim el servei
            creation_vals = {
                "pricelist_id": pricelist_id,
                "product_id": owner_product_id if gurb_vals["owner_cups"] else gurb_product_id,
                "data_inici": data_inici,
            }

            wiz_id = wiz_service_o.create(cursor, uid, creation_vals, context=context)

            context['active_ids'] = pol_ids
            wiz_service_o.create_services(cursor, uid, [wiz_id], context=context)

    _columns = {
        "active": fields.boolean("Actiu"),
        "start_date": fields.date("Data entrada GURB", required=True),
        "end_date": fields.date("Data sortida GURB",),
        "gurb_id": fields.many2one("som.gurb", "GURB", required=True, ondelete="cascade"),
        "cups_id": fields.many2one("giscedata.cups.ps", "CUPS", required=True),
        "beta_kw": fields.float(
            "Beta (kW)",
            digits=(10, 3),
            required=True,
        ),
        "extra_beta_kw": fields.float(
            "Extra Beta (kW)",
            digits=(10, 3),
            required=True,
        ),
        "beta_percentage": fields.function(
            _ff_get_beta_percentage,
            type="float",
            string="Total Beta (%)",
            digits=(12, 4),
            method=True,
        ),
        "owner_cups": fields.function(
            _ff_is_owner,
            type="boolean",
            string="Cups de la persona propietària",
            method=True
        )
    }

    _defaults = {
        "active": lambda *a: True,
        "extra_beta_kw": lambda *a: 0,
    }


SomGurbCups()
