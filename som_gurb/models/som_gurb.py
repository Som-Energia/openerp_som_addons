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

_STAGE_STATE = {
    "Esborrany": "draft",
    "Primera Obertura": "open",
    "Complet": "pending",
    "No Complet": "pending",
    "Pendent de Registre": "pending",
    "Registrat": "pending",
    "Actiu": "active",
    "Actiu no complet": "active",
    "Actiu no complet critic": "active",
    "Reobertura": "modification",
}

_REQUIRED_FIRST_OPENING_FIELDS = [  # TODO: Propietari - logo?
    "name",
    "code"
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
    # "CAU",
    "generation_power",  # TODO: No relació amb CAU?
    "has_compensation",  # TODO: D'on ho treiem?
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

    def _get_gurb_initial_stage(self, cursor, uid, context=None):
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
        if context is None:
            context = {}

        ir_model_obj = self.pool.get("ir.model.data")
        first_opening_stage_id = ir_model_obj.get_object_reference(
            cursor, uid, "som_gurb", "stage_gurb_first_opening"
        )[1]

        if first_opening_stage_id == stage_id:
            required_values = self.read(
                cursor,
                uid,
                ids[0],
                _REQUIRED_FIRST_OPENING_FIELDS,
                context=context
            )

            if not all(valor for valor in required_values.values()):
                raise osv.except_osv(
                    _("Error"),
                    _("Falta omplir camps necessaris per passar a l'estat de primera obertura."),
                )

    def change_state(self, cursor, uid, ids, stage_id, context=None):
        if context is None:
            context = {}

        stage_obj = self.pool.get("crm.case.stage")

        stage_name = stage_obj.read(cursor, uid, stage_id, ["name"])["name"]
        new_gurb_state = _STAGE_STATE[stage_name]
        self.write(cursor, uid, ids[0], {"gurb_state": new_gurb_state}, context=context)

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
        self.change_state(cursor, uid, ids, stage_id, context=context)

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

    _columns = {
        "name": fields.char("Nom GURB", size=60, required=True),
        "self_consumption_id": fields.many2one("giscedata.autoconsum", "CAU"),  # TODO: Required?
        "code": fields.char("Codi GURB", size=60, readonly=True),
        "roof_owner_id": fields.many2one("res.partner", "Propietari teulada", required=True),
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
        "gurb_state": fields.selection(_GURB_STATES, "Estat GURB", readonly=True),  # TODO: Borrar?
        "gurb_stage_id": fields.many2one(
            "crm.case.stage",
            "Etapa",
            required=True,
            domain=[("section_id.code", "=", "GURB")],
        ),
        "gurb_cups_ids": fields.one2many("som.gurb.cups", "gurb_id", "Betes", readonly=False),
        "joining_fee": fields.float("Tarifa cost adhesió"),  # TODO: New model
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
        "pricelist_id": fields.many2one("product.pricelist", "Quota mensual"),
    }
    _defaults = {
        "logo": lambda *a: False,
        "gurb_state": lambda *a: "draft",
        "gurb_stage_id": _get_gurb_initial_stage,
    }

    _sql_constraints = [(
        "self_consumption_id_uniq",
        "unique(self_consumption_id)",
        "Ja existeix un GURB per aquest autoconsum"
    )]


SomGurb()
