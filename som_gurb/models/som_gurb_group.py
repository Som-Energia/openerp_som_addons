# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

import logging

logger = logging.getLogger("openerp.{}".format(__name__))


class SomGurbGroup(osv.osv):
    _name = "som.gurb.group"
    _description = _("Grup generació urbana")

    def create(self, cursor, uid, vals, context=None):
        res_id = super(SomGurbGroup, self).create(cursor, uid, vals, context=context)

        ir_seq_obj = self.pool.get("ir.sequence")
        code = ir_seq_obj.get_next(cursor, uid, "som.gurb.group")

        self.write(cursor, uid, res_id, {"code": code}, context=context)

        return res_id

    def _ff_get_address_fields(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        address_obj = self.pool.get("res.partner.address")
        res = {}
        for gurb_vals in self.read(cursor, uid, ids, ["address_id"]):
            address_id = gurb_vals.get("address_id", False)
            if address_id:
                address = address_obj.browse(cursor, uid, address_id[0], context=context)
                res[gurb_vals["id"]] = {
                    "province": address.state_id.name if address.state_id else "",
                    "zip_code": address.zip,
                }
            else:
                res[gurb_vals["id"]] = {
                    "province": "",
                    "zip_code": "",
                }
        return res

    def _ff_total_betas(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        gurb_cups_obj = self.pool.get("som.gurb.cups")
        gurb_cau_obj = self.pool.get("som.gurb.cau")
        gurb_cups_beta_obj = self.pool.get("som.gurb.cups.beta")
        res = {}
        for gurb_group_id in ids:
            gurb_cau_ids = gurb_cau_obj.search(
                cursor, uid, [("gurb_group_id", "=", gurb_group_id)], context=context
            )
            gen_power = 0
            assigned_betas_kw = 0
            extra_betas_kw = 0
            gift_betas_kw = 0
            future_betas_kw = 0
            future_extra_betas_kw = 0
            future_gift_betas_kw = 0
            for gurb_cau_id in gurb_cau_ids:
                search_params = [
                    ("gurb_cau_id", "=", gurb_cau_id), ("state", "not in", ["cancel", "draft"])
                ]
                gurb_cups_ids = gurb_cups_obj.search(
                    cursor, uid, search_params, context=context
                )
                gurb_cups_data = gurb_cups_obj.read(
                    cursor, uid, gurb_cups_ids, ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
                )
                gen_power += gurb_cau_obj.read(
                    cursor, uid, gurb_cau_id, ["generation_power"])["generation_power"] or 0

                assigned_betas_kw = sum(gurb_cups["beta_kw"] for gurb_cups in gurb_cups_data)
                extra_betas_kw += sum(
                    gurb_cups["extra_beta_kw"] for gurb_cups in gurb_cups_data
                )
                gift_betas_kw += sum(
                    gurb_cups["gift_beta_kw"] for gurb_cups in gurb_cups_data
                )

                search_params = [
                    ("gurb_cau_id", "=", gurb_cau_id), ("state", "in", ["active", "atr_pending"])
                ]
                active_gurb_cups_ids = gurb_cups_obj.search(
                    cursor, uid, search_params, context=context
                )

                future_gurb_cups_data = gurb_cups_obj.read(
                    cursor, uid, active_gurb_cups_ids, ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
                )

                future_betas_kw += sum(
                    gurb_cups["beta_kw"] for gurb_cups in future_gurb_cups_data
                )
                future_extra_betas_kw += sum(
                    gurb_cups["extra_beta_kw"] for gurb_cups in future_gurb_cups_data
                )
                future_gift_betas_kw += sum(
                    gurb_cups["gift_beta_kw"] for gurb_cups in future_gurb_cups_data
                )

                search_params = [
                    ("gurb_cau_id", "=", gurb_cau_id),
                    ("state", "in", ["comming_modification", "comming_registration"])
                ]
                mod_gurb_cups_ids = gurb_cups_obj.search(
                    cursor, uid, search_params, context=context
                )

                search_params = [
                    ("gurb_cups_id", "in", mod_gurb_cups_ids),
                    ("future_beta", "=", True)
                ]
                mod_gurb_cups_beta_ids = gurb_cups_beta_obj.search(
                    cursor, uid, search_params, context=context
                )
                mod_future_gurb_cups_data = gurb_cups_beta_obj.read(
                    cursor, uid, mod_gurb_cups_beta_ids,
                    ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
                )

                future_betas_kw += sum(
                    gurb_cups["beta_kw"] for gurb_cups in mod_future_gurb_cups_data
                )
                future_extra_betas_kw += sum(
                    gurb_cups["extra_beta_kw"] for gurb_cups in mod_future_gurb_cups_data
                )
                future_gift_betas_kw += sum(
                    gurb_cups["gift_beta_kw"] for gurb_cups in mod_future_gurb_cups_data
                )

            assigned_betas_percentage = 0
            assigned_gift_betas_percentage = 0
            extra_betas_percentage = 0
            future_betas_percentage = 0
            future_gift_betas_percentage = 0
            future_assigned_betas_percentage = 0
            if gen_power:
                assigned_betas_percentage = (
                    assigned_betas_kw
                ) * 100 / gen_power
                assigned_gift_betas_percentage = (
                    assigned_betas_kw + gift_betas_kw
                ) * 100 / gen_power
                extra_betas_percentage = extra_betas_kw * 100 / gen_power
                future_betas_percentage = future_betas_kw * 100 / gen_power
                future_gift_betas_percentage = future_gift_betas_kw * 100 / gen_power
                future_assigned_betas_percentage = (
                    future_gift_betas_percentage + future_betas_percentage
                )

            res[gurb_group_id] = {
                "assigned_betas_kw": assigned_betas_kw,
                "assigned_betas_percentage": assigned_betas_percentage,
                "available_betas_percentage": 100 - assigned_betas_percentage,
                "assigned_gift_betas_percentage": assigned_gift_betas_percentage,
                "extra_betas_kw": extra_betas_kw,
                "extra_betas_percentage": extra_betas_percentage,
                "gift_betas_kw": gift_betas_kw,
                "future_assigned_betas_percentage": future_assigned_betas_percentage,
                "generation_power": gen_power,
            }

        return res

    _columns = {
        "gurb_cau_ids": fields.one2many("som.gurb.cau", "gurb_group_id", "Betes", readonly=False),
        "name": fields.char("Nom grup GURB", size=60, required=True),
        "code": fields.char("Codi GURB grup", size=60, readonly=True),
        "roof_owner_id": fields.many2one("res.partner", "Propietari teulada"),
        "address_id": fields.many2one("res.partner.address", "Adreça"),
        "province": fields.function(
            _ff_get_address_fields,
            type="char",
            string="Província",
            method=True,
            multi="address",
            size=64,
        ),
        "zip_code": fields.function(
            _ff_get_address_fields,
            type="char",
            string="Codi postal",
            method=True,
            multi="address",
        ),
        "notes": fields.text("Observacions"),
        "critical_incomplete_state": fields.integer("Estat crític incomplet (%)"),
        "pricelist_id": fields.many2one("product.pricelist", "Preus del GURB grup"),
        "generation_power": fields.function(
            _ff_total_betas,
            string="Potència de generació total (kW)",
            type="float",
            method=True,
            multi="betas",
        ),
        "assigned_betas_kw": fields.function(
            _ff_total_betas,
            string="Betes assignades (kW)",
            type="float",
            method=True,
            multi="betas",
        ),
        "assigned_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes assignades (%)",
            type="float",
            method=True,
            multi="betas",
        ),
        "available_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes disponibles (%)",
            type="float",
            method=True,
            multi="betas",
        ),
        "extra_betas_kw": fields.function(
            _ff_total_betas,
            string="Betes extres (kW)",
            type="float",
            method=True,
            multi="betas",
        ),
        "extra_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes extres (%)",
            type="float",
            method=True,
            multi="betas",
        ),
        "gift_betas_kw": fields.function(
            _ff_total_betas,
            string="Betes regal (kW)",
            type="float",
            method=True,
            multi="betas",
        ),
        "assigned_gift_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes assginades + regalades (%)",
            type="float",
            method=True,
            multi="betas",
        ),
        "future_assigned_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes assginades + regalades (%) propera reobertura",
            type="float",
            method=True,
            multi="betas",
        ),
        "min_power_20": fields.float("Topall min. per contracte 2.0 (kW)"),
        "max_power_20": fields.float("Topall max. per contracte 2.0 (kW)"),
        "min_power_30": fields.float("Topall min. per contracte 3.0 (kW)"),
        "max_power_30": fields.float("Topall max. per contracte 3.0 (kW)"),
    }

    _defaults = {
        "min_power_20": lambda *a: 0.5,
        "min_power_30": lambda *a: 0.5,
    }


SomGurbGroup()
