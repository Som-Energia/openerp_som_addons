# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import logging

logger = logging.getLogger("openerp.{}".format(__name__))

_GURB_STATES = [
    ("draft", "Esborrany"),
    ("open", "Obert"),
    ("pending", "Pendent"),
    ("active", "Actiu"),
    ("modification", "Modificació"),
]


class SomGurb(osv.osv):
    _name = "som.gurb"
    _inherits = {"giscedata.autoconsum": "self_consumption_id"}
    _description = _("Grup generació urbana")

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

    def _get_grub_initial_stage(self, cursor, uid, context=None):
        if context is None:
            context = {}
        ir_model_obj = self.pool.get("ir.model.data")

        stage_id = ir_model_obj.get_object_reference(
            cursor, uid, "som_gurb", "stage_gurb_draft"
        )

        if stage_id:
            return stage_id[1]

        return False

    def action_next_stage(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        order = "sequence"
        operator = ">"
        self._action_change_stage(cursor, uid, ids, order, operator, context=context)

    def action_previous_stage(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        order = "sequence desc"
        operator = "<"
        self._action_change_stage(cursor, uid, ids, order, operator, context=context)

    def validate_stage(self, cursor, uid, ids, current_stage_id, stage_id, context=None):
        pass

    def _action_change_stage(self, cursor, uid, ids, order, operator, context=None):
        if context is None:
            context = {}

        stage_obj = self.pool.get("crm.case.stage")
        ir_model_obj = self.pool.get("ir.model.data")

        section_id = ir_model_obj.get_object_reference(
            cursor, uid, "som_gurb", "gurb_crm_sections"
        )[1]

        current_stage_id = self.read(cursor, uid, ids[0], ["gurb_stage_id"])["gurb_stage_id"][0]
        stage_sequence = stage_obj.read(cursor, uid, current_stage_id, ["sequence"])["sequence"]

        last_stage_id = ir_model_obj.get_object_reference(
            cursor, uid, "som_gurb", "stage_gurb_reopened"
        )[1]

        first_stage_id = ir_model_obj.get_object_reference(
            cursor, uid, "som_gurb", "stage_gurb_draft"
        )[1]

        if current_stage_id == first_stage_id and order == "sequence desc":
            return False
        elif current_stage_id != last_stage_id or order == "sequence desc":
            search_params = [
                ("sequence", operator, stage_sequence),
                ("section_id", "=", section_id)
            ]

            stage_id = stage_obj.search(cursor, uid, search_params, order=order, context=context)[0]
        else:
            stage_id = ir_model_obj.get_object_reference(
                cursor, uid, "som_gurb", "stage_gurb_active"
            )[1]
        self.validate_stage(cursor, uid, ids, current_stage_id, stage_id, context=context)
        self.write(cursor, uid, ids[0], {"gurb_stage_id": stage_id}, context=context)

    _columns = {
        "name": fields.char("Nom GURB", size=60, required=True),
        "self_consumption_id": fields.many2one("giscedata.autoconsum", "CAU"),
        "code": fields.char("Codi GURB", size=60, required=True),
        "roof_owner_id": fields.many2one("res.partner", "Propietari teulada", required=True),
        "logo": fields.boolean("Logo"),
        "address_id": fields.many2one("res.partner.address", "Adreça", required=True),
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
        "sig_data": fields.char("Dades SIG", size=60, required=True),
        "activation_date": fields.date("Data activació GURB"),
        "gurb_state": fields.selection(_GURB_STATES, "Estat GURB", required=True),
        "gurb_stage_id": fields.many2one(
            "crm.case.stage",
            "Etapa",
            required=True,
            domain=[("section_id.code", "=", "GURB")],
        ),
        "gurb_cups_ids": fields.one2many("som.gurb.cups", "gurb_id", "Betes", readonly=False),
        "joining_fee": fields.float("Tarifa cost adhesió"),  # TODO: New model
        "service_fee": fields.float("Tarifa quota servei"),  # TODO: New model
        "max_power": fields.float("Topall max. per contracte (kW)"),
        "mix_power": fields.float("Topall mix. per contracte (kW)"),
        "critical_incomplete_state": fields.integer("Estat crític incomplet (%)"),
        "first_opening_days": fields.integer("Dies primera obertura"),
        "reopening_days": fields.integer("Dies reobertura"),
        "notes": fields.text("Observacions"),
        "history_box": fields.text("Històric del GURB", readonly=True),
        "has_compensation": fields.boolean("Amb compensació", readonly=True),
        "generation_power": fields.function(
            _ff_get_generation_power,
            type="float",
            digits=(10, 3),
            string="Potència generació",
            method=True,
        ),
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
    }
    _defaults = {
        "logo": lambda *a: False,
        "gurb_state": lambda *a: "draft",
        "gurb_stage_id": _get_grub_initial_stage,
    }

    _sql_constraints = [(
        "self_consumption_id_uniq",
        "unique(self_consumption_id)",
        "Ja existeix un GURB per aquest autoconsum"
    )]


SomGurb()
