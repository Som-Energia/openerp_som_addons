# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import logging

logger = logging.getLogger("openerp.{}".format(__name__))


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

    _columns = {
        "name": fields.char("Nom GURB", size=60, required=True),
        "self_consumption_id": fields.many2one("giscedata.autoconsum", "CAU"),
        "code": fields.char("Codi GURB", size=60, required=True),
        "roof_owner_id": fields.many2one("res.partner", "Propietari teulada", required=True),
        "logo": fields.boolean("Logo"),
        "address": fields.many2one("res.partner.address", "Adreça", required=True),
        "province": fields.char("Provincia", size=60, readonly=True),
        "zip_code": fields.char("Codi postal", size=60, readonly=True),
        "sig_data": fields.char("Dades SIG", size=60, required=True),
        "activation_date": fields.date(u"Data activació GURB", required=True),
        "gurb_state": fields.selection(
            [("state1", "Estat 1"), ("state2", "Estat 2"), ],  # TODO: States
            "Estat GURB",
            required=True,
        ),
        "gurb_cups_id": fields.one2many("som.gurb.cups", "gurb_id", "Betes", readonly=False),
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
    }
    _defaults = {
        "logo": lambda *a: False,
        "gurb_state": lambda *a: "state1",
    }

    _sql_constraints = [(
        "self_consumption_id_uniq",
        "unique(self_consumption_id)",
        "Ja existeix un GURB per aquest autoconsum"
    )]


SomGurb()
