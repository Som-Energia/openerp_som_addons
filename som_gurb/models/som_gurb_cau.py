# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime

import logging

logger = logging.getLogger("openerp.{}".format(__name__))

_GURB_STATES = [
    ("draft", "Esborrany"),
    ("first_opening", "Primera Obertura"),
    ("complete", "Complet"),
    ("incomplete", "No Complet"),
    ("registered", "Grup registrat"),
    ("in_process", "En tràmit"),
    ("active", "Actiu"),
    ("active_inc", "Actiu no complet"),
    ("active_crit_inc", "Actiu no complet critic"),
    ("reopened", "Reobertura"),
]

_REQUIRED_FIRST_OPENING_FIELDS = [
    "name",
    "code",
    "address_id",
    "province",
    "zip_code",
    "roof_owner_id",
    "pricelist_id",
    "critical_incomplete_state",
    "generation_power",
    "pricelist_id",
]


class SomGurbCau(osv.osv):
    _name = "som.gurb.cau"
    _description = _("CAU generació urbana")

    def create(self, cursor, uid, vals, context=None):
        res_id = super(SomGurbCau, self).create(cursor, uid, vals, context=context)

        code = False
        gurb_group_id = vals.get('gurb_group_id')
        if gurb_group_id:
            group_obj = self.pool.get('som.gurb.group')
            group = group_obj.browse(cursor, uid, gurb_group_id, context=context)

            if group.sequence_id:
                seq_obj = self.pool.get('ir.sequence')
                code_grup = group.code
                code_cau = seq_obj.get_id(cursor, uid, group.sequence_id.id, context=context)
                code = code_grup + "/" + code_cau

        self.write(cursor, uid, res_id, {"code": code}, context=context)

        return res_id

    def get_gurb_products_ids(self, cursor, uid, context=None):
        if context is None:
            context = {}

        imd_obj = self.pool.get("ir.model.data")

        gurb_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "product_gurb"
        )[1]
        owner_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "product_owner_gurb"
        )[1]
        enterprise_product_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "product_enterprise_gurb"
        )[1]

        product_ids = [gurb_product_id, owner_product_id, enterprise_product_id]

        return product_ids

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
        gurb_cups_beta_obj = self.pool.get("som.gurb.cups.beta")
        res = {}
        for gurb_cau_id in ids:
            search_params = [
                ("gurb_cau_id", "=", gurb_cau_id), ("state", "not in", ["cancel", "draft"])
            ]
            gurb_cups_ids = gurb_cups_obj.search(
                cursor, uid, search_params, context=context
            )
            gurb_cups_data = gurb_cups_obj.read(
                cursor, uid, gurb_cups_ids, ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
            )
            gen_power = self.read(
                cursor, uid, gurb_cau_id, ["generation_power"])["generation_power"]

            assigned_betas_kw = sum(gurb_cups["beta_kw"] for gurb_cups in gurb_cups_data)
            extra_betas_kw = sum(
                gurb_cups["extra_beta_kw"] for gurb_cups in gurb_cups_data
            )
            gift_betas_kw = sum(
                gurb_cups["gift_beta_kw"] for gurb_cups in gurb_cups_data
            )

            search_params = [
                ("gurb_cau_id", "=", gurb_cau_id), ("state", "in", ["active", "atr_pending"])
            ]
            active_gurb_cups_ids = gurb_cups_obj.search(cursor, uid, search_params, context=context)

            future_gurb_cups_data = gurb_cups_obj.read(
                cursor, uid, active_gurb_cups_ids, ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
            )

            future_betas_kw = sum(
                gurb_cups["beta_kw"] for gurb_cups in future_gurb_cups_data
            )
            future_extra_betas_kw = sum(
                gurb_cups["extra_beta_kw"] for gurb_cups in future_gurb_cups_data
            )
            future_gift_betas_kw = sum(
                gurb_cups["gift_beta_kw"] for gurb_cups in future_gurb_cups_data
            )

            search_params = [
                ("gurb_cau_id", "=", gurb_cau_id),
                ("state", "in", ["comming_modification", "comming_registration"])
            ]
            mod_gurb_cups_ids = gurb_cups_obj.search(cursor, uid, search_params, context=context)

            search_params = [
                ("gurb_cups_id", "in", mod_gurb_cups_ids),
                ("future_beta", "=", True)
            ]
            mod_gurb_cups_beta_ids = gurb_cups_beta_obj.search(
                cursor, uid, search_params, context=context
            )
            mod_future_gurb_cups_data = gurb_cups_obj.read(
                cursor, uid, mod_gurb_cups_beta_ids, ["beta_kw", "extra_beta_kw", "gift_beta_kw"]
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
            assigned_extra_betas_percentage = 0
            assigned_extra_gift_betas_percentage = 0
            assigned_gift_betas_percentage = 0
            extra_betas_percentage = 0
            future_betas_percentage = 0
            future_extra_betas_percentage = 0
            future_gift_betas_percentage = 0
            future_assigned_betas_percentage = 0
            if gen_power:
                assigned_betas_percentage = (
                    assigned_betas_kw
                ) * 100 / gen_power
                assigned_extra_betas_percentage = (
                    assigned_betas_kw + extra_betas_kw
                ) * 100 / gen_power
                assigned_extra_gift_betas_percentage = (
                    assigned_betas_kw + extra_betas_kw + gift_betas_kw
                ) * 100 / gen_power
                assigned_gift_betas_percentage = (
                    assigned_betas_kw + gift_betas_kw
                ) * 100 / gen_power
                extra_betas_percentage = extra_betas_kw * 100 / gen_power
                future_betas_percentage = future_betas_kw * 100 / gen_power
                future_extra_betas_percentage = future_extra_betas_kw * 100 / gen_power
                future_gift_betas_percentage = future_gift_betas_kw * 100 / gen_power
                future_assigned_betas_percentage = (
                    future_gift_betas_percentage + future_betas_percentage
                )

            res[gurb_cau_id] = {
                "assigned_betas_kw": assigned_betas_kw,
                "available_betas_kw": gen_power - assigned_betas_kw,
                "assigned_betas_percentage": assigned_betas_percentage,
                "assigned_gift_betas_percentage": assigned_gift_betas_percentage,
                "extra_betas_kw": extra_betas_kw,
                "extra_betas_percentage": extra_betas_percentage,
                "gift_betas_kw": gift_betas_kw,
                "assigned_extra_betas_percentage": assigned_extra_betas_percentage,
                "assigned_extra_gift_betas_percentage": assigned_extra_gift_betas_percentage,
                "available_betas_percentage": 100 - assigned_betas_percentage,
                "future_betas_kw": future_betas_kw,
                "future_extra_betas_kw": future_extra_betas_kw,
                "future_gift_betas_kw": future_gift_betas_kw,
                "future_betas_percentage": future_betas_percentage,
                "future_extra_betas_percentage": future_extra_betas_percentage,
                "future_gift_betas_percentage": future_gift_betas_percentage,
                "future_assigned_betas_percentage": future_assigned_betas_percentage
            }

        return res

    def _ff_get_self_consumption_fields(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        auto_obj = self.pool.get("giscedata.autoconsum")
        res = {}
        for gurb_vals in self.read(cursor, uid, ids, ["self_consumption_id"]):
            auto_id = gurb_vals.get("self_consumption_id", False)
            if auto_id:
                auto_vals = auto_obj.read(
                    cursor, uid, auto_id[0], ["state", "data_alta", "data_baixa"]
                )
                res[gurb_vals["id"]] = {
                    "self_consumption_state": auto_vals["state"],
                    "self_consumption_start_date": auto_vals["data_alta"],
                    "self_consumption_end_date": auto_vals["data_baixa"],
                }
            else:
                res[gurb_vals["id"]] = {
                    "self_consumption_state": False,
                    "self_consumption_start_date": False,
                    "self_consumption_end_date": False,
                }
        return res

    def change_state(self, cursor, uid, ids, new_state, context=None):
        write_values = {
            "state": new_state,
            "state_date": datetime.now().strftime("%Y-%m-%d")
        }
        for record_id in ids:
            self.write(cursor, uid, ids, write_values, context=context)

    def validate_complete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return (
                record.assigned_betas_kw == record.generation_power
            )

    def validate_incomplete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return (
                record.assigned_betas_kw != record.generation_power
            )

    def validate_draft_first_opening(self, cursor, uid, ids, context=None):
        for record in self.read(cursor, uid, ids, _REQUIRED_FIRST_OPENING_FIELDS, context=context):
            for k, v in record.items():
                if not v:
                    raise osv.except_osv(
                        _("Error al canviar d'estat"),
                        _("Per poder obrir el GURB CAU s'ha d'omplir el camp: {}".format(k))
                    )
            return True

    def validate_active_critic_incomplete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return record.assigned_betas_percentage < record.critical_incomplete_state

    def activate_gurb_from_m1_05(self, cursor, uid, sw_id, activation_date, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")

        gurb_cau_id = self.get_gurb_from_sw_id(cursor, uid, sw_id, context=context)
        gurb_cups_id = gurb_cups_obj.get_gurb_cups_from_sw_id(cursor, uid, sw_id, context=context)
        gurb_cups_obj.activate_or_modify_gurb_cups(
            cursor, uid, gurb_cups_id, activation_date, context=context)
        gurb_cups_obj.send_gurb_activation_email(cursor, uid, [gurb_cups_id], context=None)
        gurb_date = self.read(cursor, uid, gurb_cau_id, ["activation_date"])["activation_date"]
        if not gurb_date:
            write_vals = {
                "activation_date": activation_date
            }
            self.write(cursor, uid, gurb_cau_id, write_vals, context=context)

    def get_gurb_from_sw_id(self, cursor, uid, sw_id, context=None):
        if context is None:
            context = {}

        switching_obj = self.pool.get("giscedata.switching")

        pol_id = switching_obj.read(
            cursor, uid, sw_id, ["cups_polissa_id"], context=context)["cups_polissa_id"][0]

        return self.get_gurb_from_pol_id(cursor, uid, pol_id, context=context)

    def get_gurb_from_pol_id(self, cursor, uid, pol_id, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")

        search_params = [
            ("polissa_id", "=", pol_id)
        ]

        gurb_cups_ids = gurb_cups_obj.search(cursor, uid, search_params, context=context)

        if len(gurb_cups_ids) == 1:
            gurb_cau_id = gurb_cups_obj.read(
                cursor, uid, gurb_cups_ids[0], ["gurb_cau_id"], context=context
            )["gurb_cau_id"][0]

        return gurb_cau_id

    def add_services_to_gurb_contracts(self, cursor, uid, ids, activation_date, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")

        for gurb_cups_id in ids:
            search_params = [("gurb_cups_id", "=", gurb_cups_id)]
            gurb_cups_ids = gurb_cups_obj.search(cursor, uid, search_params, context=context)
            gurb_cups_obj.add_service_to_contract(
                cursor, uid, gurb_cups_ids, activation_date, context=context)

        return True

    def _related_attachments(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        res = dict.fromkeys(ids, False)
        attach_obj = self.pool.get("ir.attachment")
        for gurb_cau_id in ids:
            attach_ids = attach_obj.search(cursor, uid, [
                ("res_model", "=", "som.gurb.cau"),
                ("res_id", "=", gurb_cau_id)
            ])
            res[gurb_cau_id] = list(set(attach_ids))
        return res

    _columns = {
        "name": fields.char("Nom GURB CAU", size=60, required=True),
        "self_consumption_id": fields.many2one("giscedata.autoconsum", "CAU"),
        "code": fields.char("Codi GURB CAU", size=60, readonly=True),
        "producer": fields.many2one("res.partner", "Productora"),
        "cil": fields.char("Codi CIL", size=60),
        "roof_owner_id": fields.many2one("res.partner", "Propietari teulada"),
        "logo": fields.boolean("Logo"),
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
        "sig_data": fields.char("Dades SIG", size=60),
        "activation_date": fields.date("Data activació GURB CAU"),
        "state": fields.selection(_GURB_STATES, "Estat del GURB CAU", readonly=True),
        "state_date": fields.date("Data activació estat", readonly=True),
        "gurb_cups_ids": fields.one2many("som.gurb.cups", "gurb_cau_id", "Betes", readonly=False),
        "critical_incomplete_state": fields.integer("Estat crític incomplet (%)"),
        "notes": fields.text("Observacions"),
        "history_box": fields.text("Històric del GURB CAU", readonly=True),
        "has_compensation": fields.boolean("Amb compensació"),  # Selection?
        "generation_power": fields.float("Potència generació", digits=(10, 3)),
        "meter_id": fields.many2one("giscedata.registrador", "Registrador (comptador)"),
        "available_betas_kw": fields.function(
            _ff_total_betas,
            string="Betes disponibles (kW)",
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
        "available_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes disponibles (%)",
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
        "assigned_extra_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes assginades + extres (%)",
            type="float",
            method=True,
            multi="betas",
        ),
        "assigned_extra_gift_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes assginades + extres + regalades (%)",
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
        "self_consumption_state": fields.function(
            _ff_get_self_consumption_fields,
            type="char",
            size=30,
            string="Estat",
            method=True,
            multi="self_consumption"
        ),
        "self_consumption_start_date": fields.function(
            _ff_get_self_consumption_fields,
            type="date",
            string="Data alta",
            method=True,
            multi="self_consumption",
        ),
        "self_consumption_end_date": fields.function(
            _ff_get_self_consumption_fields,
            type="date",
            string="Data baixa",
            method=True,
            multi="self_consumption",
        ),
        "related_attachments": fields.function(
            _related_attachments,
            method=True,
            string="Adjunts relacionats",
            type="one2many",
            relation="ir.attachment"
        ),
        "pricelist_id": fields.many2one("product.pricelist", "Preus del GURB CAU"),
        "initial_product_id": fields.many2one("product.product", "Producte quota inicial"),
        "quota_product_id": fields.many2one("product.product", "Producte base quota mensual"),
        "gurb_group_id": fields.many2one(
            "som.gurb.group", "GURB grup", required=True, ondelete="cascade"),
    }

    _defaults = {
        "logo": lambda *a: False,
        "state": lambda *a: "draft",
    }

    _sql_constraints = [(
        "self_consumption_id_uniq",
        "unique(self_consumption_id)",
        "Ja existeix un GURB CAU per aquest autoconsum"
    )]


SomGurbCau()
