# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime, date, timedelta

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
    "max_power",
    "min_power",
    "first_opening_days",
    "reopening_days",
    "critical_incomplete_state",
    "generation_power",
    "pricelist_id",
]


class SomGurb(osv.osv):
    _name = "som.gurb"
    _description = _("Grup generació urbana")

    def create(self, cursor, uid, vals, context=None):
        res_id = super(SomGurb, self).create(cursor, uid, vals, context=context)

        ir_seq = self.pool.get("ir.sequence")
        code = ir_seq.get_next(cursor, uid, "som.gurb")

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
        res = {}
        for gurb_id in ids:
            gurb_cups_ids = gurb_cups_obj.search(cursor, uid, [("gurb_id", "=", gurb_id)])
            gurb_cups_data = gurb_cups_obj.read(
                cursor, uid, gurb_cups_ids, ["beta_kw", "extra_beta_kw"]
            )
            gen_power = self.read(cursor, uid, gurb_id, ["generation_power"])["generation_power"]

            assigned_betas_kw = sum(gurb_cups["beta_kw"] for gurb_cups in gurb_cups_data)
            extra_betas_kw = sum(
                gurb_cups["extra_beta_kw"] for gurb_cups in gurb_cups_data
            )
            assigned_betas_percentage = 0
            assigned_extra_betas_percentage = 0
            if gen_power:
                assigned_betas_percentage = (
                    assigned_betas_kw
                ) * 100 / gen_power
                assigned_extra_betas_percentage = (
                    assigned_betas_kw + extra_betas_kw
                ) * 100 / gen_power

            res[gurb_id] = {
                "assigned_betas_kw": assigned_betas_kw,
                "available_betas_kw": gen_power - assigned_betas_kw,
                "assigned_betas_percentage": assigned_betas_percentage,
                "extra_betas_kw": extra_betas_kw,
                "assigned_extra_betas_percentage": assigned_extra_betas_percentage,
                "available_betas_percentage": 100 - assigned_betas_percentage,
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

    def _is_reopening_end_date(self, cursor, uid, record, context=None):
        state_date = datetime.strptime(record.state_date, '%Y-%m-%d').date()
        reopening_end_date = state_date + timedelta(days=record.reopening_days)
        today = date.today()

        return today >= reopening_end_date

    def _is_first_opening_end_date(self, cursor, uid, record, context=None):
        state_date = datetime.strptime(record.state_date, '%Y-%m-%d').date()
        opening_end_date = state_date + timedelta(days=record.first_opening_days)
        today = date.today()

        return today >= opening_end_date

    def validate_first_opening_complete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return (
                self._is_first_opening_end_date(cursor, uid, record)
                and record.assigned_betas_kw == record.generation_power
            )

    def validate_first_opening_incomplete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return (
                self._is_first_opening_end_date(cursor, uid, record)
                and record.assigned_betas_kw != record.generation_power
            )

    def validate_reopening_complete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return (
                self._is_reopening_end_date(cursor, uid, record)
                or record.assigned_betas_kw == record.generation_power
            )

    def validate_reopening_incomplete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return (
                self._is_reopening_end_date(cursor, uid, record)
                and record.assigned_betas_kw != record.generation_power
            )

    def validate_incomplete_complete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return record.assigned_betas_kw == record.generation_power

    def validate_draft_first_opening(self, cursor, uid, ids, context=None):
        for record in self.read(cursor, uid, ids, _REQUIRED_FIRST_OPENING_FIELDS, context=context):
            for k, v in record.items():
                if not v:
                    raise osv.except_osv(
                        _("Error al canviar d'estat"),
                        _("Per poder obrir el GURB s'ha d'omplir el camp: {}".format(k))
                    )
            return True

    def validate_active_incomplete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return record.assigned_betas_kw != record.generation_power

    def validate_active_critic_incomplete(self, cursor, uid, ids, context=None):
        for record in self.browse(cursor, uid, ids, context=context):
            return record.assigned_betas_percentage < record.critical_incomplete_state

    # WIP CODE
    def add_services_to_gurb_contracts(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")
        ir_model_obj = self.pool.get("ir.model.data")

        for gurb_id in ids:
            pricelist_id = self.read(
                cursor, uid, gurb_id, ["pricelist_id"], context=context
            )["pricelist_id"]

            product_id = ir_model_obj.get_object_reference(
                cursor, uid, "som_gurb", "product_gurb"
            )

            search_params = [
                ("gurb_id", "=", gurb_id)
            ]
            gurb_cups_ids = gurb_cups_obj.search(
                cursor, uid, search_params, context=context
            )
            gurb_cups_obj.add_service_to_contract(
                cursor, uid, gurb_cups_ids, pricelist_id, product_id, context=context
            )

        return True

    def _related_attachments(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        res = dict.fromkeys(ids, False)
        attach_obj = self.pool.get("ir.attachment")
        for gurb_id in ids:
            attach_ids = attach_obj.search(cursor, uid, [
                ("res_model", "=", "som.gurb"),
                ("res_id", "=", gurb_id)
            ])
            res[gurb_id] = list(set(attach_ids))
        return res

    _columns = {
        "name": fields.char("Nom GURB", size=60, required=True),
        "self_consumption_id": fields.many2one("giscedata.autoconsum", "CAU"),
        "code": fields.char("Codi GURB", size=60, readonly=True),
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
        "activation_date": fields.date("Data activació GURB"),
        "state": fields.selection(_GURB_STATES, "Estat del GURB", readonly=True),
        "state_date": fields.date("Data activació estat", readonly=True),
        "gurb_cups_ids": fields.one2many("som.gurb.cups", "gurb_id", "Betes", readonly=False),
        "max_power": fields.float("Topall max. per contracte (kW)"),
        "min_power": fields.float("Topall min. per contracte (kW)"),
        "critical_incomplete_state": fields.integer("Estat crític incomplet (%)"),
        "first_opening_days": fields.integer("Dies primera obertura"),
        "reopening_days": fields.integer("Dies reobertura"),
        "notes": fields.text("Observacions"),
        "history_box": fields.text("Històric del GURB", readonly=True),
        "has_compensation": fields.boolean("Amb compensació", readonly=True),  # Selection?
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
        "assigned_extra_betas_percentage": fields.function(
            _ff_total_betas,
            string="Betes assginades + extres (%)",
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
        "pricelist_id": fields.many2one("product.pricelist", "Preus del GURB"),
    }
    _defaults = {
        "logo": lambda *a: False,
        "state": lambda *a: "draft",
    }

    _sql_constraints = [(
        "self_consumption_id_uniq",
        "unique(self_consumption_id)",
        "Ja existeix un GURB per aquest autoconsum"
    )]


SomGurb()
