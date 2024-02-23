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
    "joining_fee",
    "pricelist_id",
    "max_power",
    "mix_power",
    "first_opening_days",
    "reopening_days",
    "critical_incomplete_state",
    "generation_power",
    # "has_compensation",
]


class SomGurbStateLog(osv.osv):
    # TODO: Use this model or a field for the current state start date + text log?

    _name = "som.gurb.state.log"
    _order = "create_date desc"

    def create(self, cursor, uid, vals, context=None):
        res_id = super(SomGurbStateLog, self).create(cursor, uid, vals, context=context)

        if res_id:
            # If exists, set date_end to the previous state log with same "gurb_id"
            new_state_log = self.browse(cursor, uid, res_id, context=context)
            prev_state_log_ids = self.search(
                cursor, uid, [("gurb_id", "=", new_state_log.gurb_id.id)], context=context
            )
            if len(prev_state_log_ids) > 1:
                self.write(
                    cursor,
                    uid,
                    prev_state_log_ids[1],
                    {"date_end": new_state_log.date_start},
                    context=context,
                )

        return res_id

    _columns = {
        "gurb_id": fields.many2one("som.gurb", "GURB", required=True),
        "state": fields.char("Estat", size=60, required=True),
        "date_start": fields.date("Data inici", required=True),
        "date_end": fields.date("Data final"),
    }

    _defaults = {
        "date_start": lambda *a: datetime.now().strftime("%Y-%m-%d"),
    }


SomGurbStateLog()


class SomGurb(osv.osv):
    _name = "som.gurb"
    _description = _("Grup generació urbana")

    def create(self, cursor, uid, vals, context=None):
        res_id = super(SomGurb, self).create(cursor, uid, vals, context=context)

        ir_seq = self.pool.get("ir.sequence")
        code = ir_seq.get_next(cursor, uid, "som.gurb")

        self.write(cursor, uid, res_id, {"code": code}, context=context)

        return res_id

    def _ff_get_generation_power(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        auto_obj = self.pool.get("giscedata.autoconsum")
        res = dict.fromkeys(ids, False)
        for gurb_vals in self.read(cursor, uid, ids, ["self_consumption_id"]):
            auto_id = gurb_vals.get("self_consumption_id", False)
            if auto_id:
                autoconsum = auto_obj.browse(cursor, uid, auto_id[0], context=context)
                max_gen_pot = 0
                try:
                    gens = autoconsum.generador_id
                    for gen in gens:
                        max_gen_pot = max(max_gen_pot, gen.pot_instalada_gen)
                except Exception as e:
                    logger.info(
                        _(
                            u"Error: No s'ha pogut trobar la instal·lació d'Autoconsum. "
                            u"No es pot recuperar la potència de generació. e: {}"
                        ).format(e)
                    )
                finally:
                    res[gurb_vals["id"]] = max_gen_pot
        return res

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
            gurb_cups_data = gurb_cups_obj.read(cursor, uid, gurb_cups_ids, ["beta_kw"])
            gen_power = self.read(cursor, uid, gurb_id, ["generation_power"])["generation_power"]

            assigned_betas_kw = sum(gurb_cups["beta_kw"] for gurb_cups in gurb_cups_data)
            assigned_betas_percentage = (assigned_betas_kw * 100 / gen_power) if gen_power else 0

            res[gurb_id] = {
                "assigned_betas_kw": assigned_betas_kw,
                "available_betas_kw": gen_power - assigned_betas_kw,
                "assigned_betas_percentage": assigned_betas_percentage,
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

    def _log_change_state(self, cursor, uid, id, new_state, context=None):
        self.write(cursor, uid, id, {"state_log_ids": [(0, 0, {"state": new_state})]})

    def change_state(self, cursor, uid, ids, new_state, context=None):
        for record_id in ids:
            self.write(cursor, uid, ids, {"state": new_state}, context=context)
            self._log_change_state(cursor, uid, record_id, new_state, context=context)

    def _is_first_opening_end_date(self, cursor, uid, record, context=None):
        if not record.state_log_ids[0]:
            raise osv.except_osv(
                _("No hi ha logs dels canvis d'estat"),
                _("Hi ha d'haver almenys un registre en els logs de canvis d'estat"),
            )

        if record.state_log_ids[0].state != "first_opening":
            raise osv.except_osv(
                _("Error a l'obtenir el registre més recent"),
                _("El registre més recent ha de ser de l'estat Primera Obertura"),
            )

        state_date_start_str = record.state_log_ids[0].date_start
        state_date_start = datetime.strptime(state_date_start_str, '%Y-%m-%d').date()
        max_opening_date = state_date_start + timedelta(days=record.first_opening_days)
        today = date.today()

        return today >= max_opening_date

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

    def validate_draft_first_opening(self, cursor, uid, ids, context=None):
        for record in self.read(cursor, uid, ids, _REQUIRED_FIRST_OPENING_FIELDS, context=context):
            return all(valor for valor in record.values())

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
        "gurb_cups_ids": fields.one2many("som.gurb.cups", "gurb_id", "Betes", readonly=False),
        "state_log_ids": fields.one2many(
            "som.gurb.state.log",
            "gurb_id",
            "Logs canvi d'estat",
            readonly=True,
        ),
        "joining_fee": fields.float("Tarifa cost adhesió"),  # TODO: New model
        "max_power": fields.float("Topall max. per contracte (kW)"),
        "mix_power": fields.float("Topall mix. per contracte (kW)"),
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
        "pricelist_id": fields.many2one("product.pricelist", "Quota mensual"),
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
